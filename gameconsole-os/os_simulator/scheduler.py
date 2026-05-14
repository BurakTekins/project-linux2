# Implements scheduling algorithms like FIFO and Round Robin

from collections import deque
from typing import Optional
from os_simulator.process_manager import PCB, ProcessManager
from os_simulator.logger import log, tick
from os_simulator import config

class FIFOScheduler:
    # Baseline: runs processes in arrival order, no preemption
    # Chosen: FIFO as the baseline scheduling algorithm.
    # Alternative considered: Shortest Job First.
    # Rejected because: We cannot reliably predict burst times for dynamic tasks like user input.
    # Trade-off accepted: Less efficient average turnaround time in favor of implementation simplicity.
    def __init__(self):
        # Initializes an empty queue and active system state
        self.queue = deque()
        self.active_process = None

    def add_process(self, pcb: PCB):
        # Adds process to end of queue and ensures state is ready
        pcb.state = "ready"
        self.queue.append(pcb)

    def next_process(self) -> Optional[PCB]:
        # Returns the current running process or pulls the next one from the ready queue
        if self.active_process:
            return self.active_process
        if not self.queue:
            log("Scheduler", "Ready queue empty — CPU idle")
            return None
        
        # Pop next process to run
        self.active_process = self.queue.popleft()
        self.active_process.state = "running"
        from os_simulator import logger
        if self.active_process.start_tick == -1:
            self.active_process.start_tick = logger.current_tick
        if self.active_process.first_response_tick == -1:
            self.active_process.first_response_tick = logger.current_tick
        log("Scheduler", f"FIFO selected {self.active_process.name}")
        return self.active_process

    def tick(self, pcb: PCB) -> bool:
        # Runs process for 1 tick, returns True if finished
        for queued_pcb in self.queue:
            queued_pcb.wait_time += 1
            
        tick()  # Increment global check
        pcb.remaining_time -= 1
        pcb.pc += 1
        log("Scheduler", f"{pcb.name} running | remaining: {pcb.remaining_time} ticks")
        
        if pcb.remaining_time <= 0:
            self.active_process = None
            return True
        return False

    def handle_blocked(self, pcb: PCB, reason: str, process_manager: ProcessManager):
        # Removes process from ready queue and updates its state to blocked via process_manager
        if pcb in self.queue:
            self.queue.remove(pcb)
        if self.active_process == pcb:
            self.active_process = None
            
        process_manager.block_process(pcb.pid, reason)
        log("Scheduler", f"{pcb.name} removed from queue — blocked: {reason}")


class RoundRobinScheduler:
    # Enhanced: preemptive, uses TIME_QUANTUM from config.py
    # Chosen: Round Robin preemptive scheduling.
    # Alternative considered: Multilevel Feedback Queue.
    # Rejected because: The added dimension of priority aging complicates the small simulation beyond necessity.
    # Trade-off accepted: Some starvation or excessive context-switching overhead relative to MLFQ.
    def __init__(self):
        # Initializes an empty queue, tracks active process and current quantum limit
        self.queue = deque()
        self.active_process = None
        self.current_quantum = 0

    def add_process(self, pcb: PCB):
        # Adds process to end of queue
        pcb.state = "ready"
        self.queue.append(pcb)

    def next_process(self) -> Optional[PCB]:
        # Returns next process from the queue and resets the quantum timer
        if self.active_process:
            return self.active_process
        if not self.queue:
            log("Scheduler", "Ready queue empty — CPU idle")
            return None
            
        self.active_process = self.queue.popleft()
        self.active_process.state = "running"
        from os_simulator import logger
        if self.active_process.start_tick == -1:
            self.active_process.start_tick = logger.current_tick
        if self.active_process.first_response_tick == -1:
            self.active_process.first_response_tick = logger.current_tick
        self.current_quantum = config.TIME_QUANTUM
        log("Scheduler", f"RR selected {self.active_process.name} | quantum: {self.current_quantum}")
        return self.active_process

    def tick(self, pcb: PCB) -> bool:
        # Runs 1 tick, checks quantum expiry, handles context switching
        for queued_pcb in self.queue:
            queued_pcb.wait_time += 1
            
        tick()  # Increment global check
        pcb.remaining_time -= 1
        pcb.pc += 1
        self.current_quantum -= 1
        log("Scheduler", f"{pcb.name} running | remaining: {pcb.remaining_time} ticks")
        
        if pcb.remaining_time <= 0:
            self.active_process = None
            return True
            
        if self.current_quantum <= 0:
            log("Scheduler", f"Context switch — {pcb.name} preempted, {pcb.remaining_time} ticks remaining")
            pcb.state = "ready"
            self.queue.append(pcb)
            self.active_process = None
            
        return False

    def handle_blocked(self, pcb: PCB, reason: str, process_manager: ProcessManager):
        # Removes process from ready queue and updates its state to blocked via process_manager
        if pcb in self.queue:
            self.queue.remove(pcb)
        if self.active_process == pcb:
            self.active_process = None
            
        process_manager.block_process(pcb.pid, reason)
        log("Scheduler", f"{pcb.name} removed from queue — blocked: {reason}")


def get_scheduler(mode: str):
    # Returns FIFOScheduler or RoundRobinScheduler based on config.SCHEDULER_MODE
    if mode == "FIFO":
        return FIFOScheduler()
    elif mode == "RR":
        return RoundRobinScheduler()
    raise ValueError(f"Unknown scheduling mode: {mode}")