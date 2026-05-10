# Handles Process Control Blocks (PCB), process creation, and termination

from dataclasses import dataclass, field
from typing import List, Optional
from os_simulator.logger import log

@dataclass
class PCB:
    pid: int
    name: str
    state: str          # "ready", "running", "blocked", "terminated"
    priority: int       # 1 (low) to 5 (high)
    pc: int             # program counter (tick count)
    memory_frames: list # list of frame numbers assigned to this process
    burst_time: int     # total ticks this process needs
    remaining_time: int # ticks left
    start_tick: int = -1    # tick when process first ran
    end_tick: int = -1      # tick when process terminated
    wait_time: int = 0      # ticks spent in ready queue, not running
    first_response_tick: int = -1  # tick when process first got CPU for the first time

class ProcessManager:
    def __init__(self):
        # Initializes the process manager with empty processes dictionary
        self.processes = {}
        self.next_pid = 1

    def create_process(self, name: str, burst_time: int, priority: int) -> PCB:
        # Creates a new PCB, assigns a pid, sets state to "ready", and logs creation
        pid = self.next_pid
        self.next_pid += 1
        pcb = PCB(pid=pid, name=name, state="ready", priority=priority, pc=0, memory_frames=[], burst_time=burst_time, remaining_time=burst_time)
        self.processes[pid] = pcb
        log("Scheduler", f"Process {name} created with PID {pid}")
        return pcb

    def terminate_process(self, pid: int):
        # Sets state to "terminated", frees memory_frames list, logs termination
        from os_simulator import logger
        pcb = self.processes.get(pid)
        if pcb:
            pcb.state = "terminated"
            pcb.end_tick = logger.current_tick
            pcb.memory_frames.clear()
            log("Scheduler", f"Process {pcb.name} terminated")

    def block_process(self, pid: int, reason: str):
        # Sets state to "blocked", logs reason
        pcb = self.processes.get(pid)
        if pcb:
            pcb.state = "blocked"
            log("Scheduler", f"Process {pcb.name} blocked: {reason}")

    def unblock_process(self, pid: int):
        # Sets state back to "ready", logs it
        pcb = self.processes.get(pid)
        if pcb:
            pcb.state = "ready"
            log("Scheduler", f"Process {pcb.name} unblocked")

    def get_process(self, pid: int) -> Optional[PCB]:
        # Returns PCB by pid
        return self.processes.get(pid)

    def list_processes(self) -> List[PCB]:
        # Returns all non-terminated processes
        return [p for p in self.processes.values() if p.state != "terminated"]

    def list_all_processes(self) -> List[PCB]:
        # Returns all processes including terminated ones
        return list(self.processes.values())