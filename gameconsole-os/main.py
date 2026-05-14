# Entry point — runs the full Game Console OS simulation

from os_simulator.process_manager import ProcessManager
from os_simulator.scheduler import get_scheduler
from os_simulator.memory_manager import MemoryManager
from os_simulator.file_system import FileSystem
from os_simulator.concurrency import SimpleLock, DeadlockDetector
from os_simulator.logger import log, section, print_process_table, print_memory_table, print_timeline, event_log_global
from os_simulator import config

def run_deadlock_demo(pm, mm, scheduler, detector):
    # Demonstrates our engineering challenge: a classic cyclic deadlock
    save_mgr = pm.create_process("SaveManager", burst_time=5, priority=2)
    game_eng = pm.create_process("GameEngine",  burst_time=5, priority=5)

    fs = FileSystem()
    mem_lock = SimpleLock("MemoryBus")

    fs.create_file(save_mgr, "save_data.bin")

    # Step 1: SaveManager acquires file lock
    fs.lock.acquire(save_mgr)
    detector.register_hold(save_mgr.pid, "FileSystem")
    log("OS", "SaveManager holds FileSystem lock")

    # Step 2: GameEngine acquires memory lock
    mem_lock.acquire(game_eng)
    detector.register_hold(game_eng.pid, "MemoryBus")
    log("OS", "GameEngine holds MemoryBus lock")

    # Step 3: SaveManager tries to get memory lock — blocked
    acquired = mem_lock.acquire(save_mgr)
    if not acquired:
        detector.register_wait(save_mgr.pid, "MemoryBus")
        log("OS", "SaveManager waiting for MemoryBus")

    # Step 4: GameEngine tries to get file lock — blocked
    acquired = fs.lock.acquire(game_eng)
    if not acquired:
        detector.register_wait(game_eng.pid, "FileSystem")
        log("OS", "GameEngine waiting for FileSystem lock")

    # Step 5: Detect deadlock
    deadlocks = detector.detect()
    if deadlocks:
        log("OS", "Deadlock confirmed. Resolving by terminating lowest priority process.")
        # Resolve: terminate priority 2 SaveManager
        pm.terminate_process(save_mgr.pid)
        fs.lock.release(save_mgr)
        detector.clear(save_mgr.pid)
        log("OS", "SaveManager terminated. GameEngine can now proceed.")


def run_simulation(mode: str) -> list:
    # Primary driver setting up all systems and running the main loops
    pm = ProcessManager()
    mm = MemoryManager()
    scheduler = get_scheduler(mode)
    detector = DeadlockDetector()

    log("OS", f"Simulation started — mode: {mode}")
    mm.status()

    process_configs = [
        ("GameEngine",   10, 5, 4),
        ("AudioManager", 6,  3, 2),
        ("InputHandler", 4,  4, 2),
        ("SaveManager",  7,  2, 3),
    ]

    for name, burst, priority, frames in process_configs:
        pcb = pm.create_process(name, burst_time=burst, priority=priority)
        allocated = mm.allocate(pcb, frames)
        if not allocated:
            mm.handle_exhaustion(pcb, scheduler, pm)
        else:
            scheduler.add_process(pcb)

    while True:
        pcb = scheduler.next_process()
        if pcb is None:
            break
            
        finished = scheduler.tick(pcb)
        
        print_process_table(pm.list_all_processes())
        print_memory_table(mm.frames)
        print("-" * 50)
        
        if finished:
            mm.deallocate(pcb)
            pm.terminate_process(pcb.pid)

    mm.status()
    log("OS", f"All processes completed. {mode} Simulation done.")
    return pm.list_all_processes()


if __name__ == "__main__":
    from os_simulator import logger

    logger.section("Game Console OS — FIFO Baseline Run")
    fifo_processes = run_simulation("FIFO")

    # reset tick for clean RR run
    logger.current_tick = 0
    logger.event_log_global.clear()

    logger.section("Game Console OS — Round Robin Enhanced Run")
    rr_processes = run_simulation("RR")

    logger.section("Baseline vs Enhanced — Scheduler Comparison")
    logger.print_comparison_table(fifo_processes, rr_processes)

    logger.section("Engineering Challenge — Deadlock Demo")
    
    # Needs some basic instances specifically just for demo functionality
    pm = ProcessManager()
    mm = MemoryManager()
    scheduler = get_scheduler(config.SCHEDULER_MODE)
    detector = DeadlockDetector()
    run_deadlock_demo(pm, mm, scheduler, detector)

    logger.section("Simulation Timeline (Round Robin Mode + Deadlock)")
    logger.print_timeline(logger.event_log_global)

