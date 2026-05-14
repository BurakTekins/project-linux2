# Manages locks, condition variables, and solves classical concurrency problems

from typing import Optional, List, Tuple, Dict
from os_simulator.process_manager import PCB
from os_simulator.logger import log

class SimpleLock:
    # Chosen: Mutex style lock for exclusive resource access.
    # Alternative considered: Counting Semaphores or Read-Write locks.
    # Rejected because: Read-Write locks are overkill for this simple file/memory bus structure.
    # Trade-off accepted: Less granular concurrency for reads if we enforced it, though we left reads unlocked for simplicity here.
    def __init__(self, name: str):
        # Initializes lock targeting the given resource name
        self.name = name
        self.owner_pid: Optional[int] = None
        self.waiting: List[PCB] = []

    def acquire(self, pcb: PCB) -> bool:
        # Tries to acquire the lock and logs the status
        if self.owner_pid is None:
            self.owner_pid = pcb.pid
            log("Concurrency", f"{pcb.name} acquired lock '{self.name}'")
            return True
        else:
            self.waiting.append(pcb)
            # Find owner name if possible (purely for logging) - assume known context though we only have owner_pid
            log("Concurrency", f"{pcb.name} waiting for lock '{self.name}' (held by process {self.owner_pid})")
            log("Concurrency", f"Lock '{self.name}' — waiting queue length: {len(self.waiting)}")
            return False

    def release(self, pcb: PCB) -> Optional[PCB]:
        # Releases the lock if the caller is the owner
        if self.owner_pid == pcb.pid:
            log("Concurrency", f"{pcb.name} released lock '{self.name}'")
            if self.waiting:
                next_pcb = self.waiting.pop(0)
                self.owner_pid = next_pcb.pid
                log("Concurrency", f"Lock '{self.name}' handed to {next_pcb.name}")
                return next_pcb
            else:
                self.owner_pid = None
        return None

    def is_locked(self) -> bool:
        # Returns True if currently held
        return self.owner_pid is not None

class DeadlockDetector:
    def __init__(self):
        # Initializes graphs to record waits and holds for deadlock detection
        self.hold_graph: Dict[int, str] = {}
        self.wait_graph: Dict[int, str] = {}

    def register_hold(self, pid: int, lock_name: str):
        # Records that a process holds a lock
        self.hold_graph[pid] = lock_name

    def register_wait(self, pid: int, lock_name: str):
        # Records that a process is waiting for a lock
        self.wait_graph[pid] = lock_name

    def clear(self, pid: int):
        # Removes tracking data for the given process
        self.hold_graph.pop(pid, None)
        self.wait_graph.pop(pid, None)

    def detect(self) -> List[Tuple[int, int]]:
        # Detects circular waits between processes
        deadlocks = []
        seen = set()  # track pairs to avoid duplicates

        for pid_a, lock_a in self.wait_graph.items():
            for pid_b, lock_b in self.wait_graph.items():
                if pid_a == pid_b:
                    continue
                # A waits for lock_b, B holds lock_b, B waits for lock_a, A holds lock_a
                if (
                    self.hold_graph.get(pid_b) == lock_a and
                    self.hold_graph.get(pid_a) == lock_b
                ):
                    pair = tuple(sorted([pid_a, pid_b]))
                    if pair not in seen:
                        seen.add(pair)
                        deadlocks.append((pid_a, pid_b))
                        log("Concurrency", f"DEADLOCK detected between PID {pid_a} and PID {pid_b}")

        return deadlocks