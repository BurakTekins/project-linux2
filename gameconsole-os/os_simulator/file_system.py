# Simulates file operations like create, read, write, and delete

from typing import Optional, Dict
from os_simulator.process_manager import PCB
from os_simulator.concurrency import SimpleLock, DeadlockDetector
from os_simulator.logger import log

class FileSystem:
    # Chosen: Non-exclusive read, exclusive write file system locking.
    # Alternative considered: Two-phase locking protocol.
    # Rejected because: Overhead of reader/writer locks is too heavy for a simple console OS context.
    # Trade-off accepted: Writers can potentially be starved if reads are excessive, but reads do not block each other here.
    def __init__(self):
        # Initializes an empty mock drive and the global FileSystem lock
        self.files: Dict[str, dict] = {}
        self.lock = SimpleLock("FileSystem")

    def create_file(self, pcb: PCB, filename: str) -> bool:
        # Creates a file if it doesn't exist
        if filename in self.files:
            return False
        self.files[filename] = {"name": filename, "content": "", "owner_pid": None}
        log("FileSystem", f"{pcb.name} created file '{filename}'")
        log("FileSystem", f"Files in system: {len(self.files)}")
        return True

    def write_file(self, pcb: PCB, filename: str, content: str, scheduler, process_manager, detector: DeadlockDetector) -> bool:
        # Acquires file lock to securely write contents, blocks process otherwise
        if self.lock.acquire(pcb):
            detector.register_hold(pcb.pid, "FileSystem")
            if filename in self.files:
                self.files[filename]["content"] += content
                self.files[filename]["owner_pid"] = pcb.pid
            log("FileSystem", f"{pcb.name} wrote to '{filename}'")
            return True
        else:
            log("FileSystem", f"{pcb.name} blocked waiting for file lock")
            detector.register_wait(pcb.pid, "FileSystem")
            scheduler.handle_blocked(pcb, "waiting for file lock", process_manager)
            return False

    def read_file(self, pcb: PCB, filename: str) -> Optional[str]:
        # Reads file content without locking
        if filename in self.files:
            log("FileSystem", f"{pcb.name} read '{filename}'")
            return self.files[filename]["content"]
        return None

    def delete_file(self, pcb: PCB, filename: str) -> bool:
        # Removes a file from the virtual file system
        if filename in self.files:
            del self.files[filename]
            log("FileSystem", f"{pcb.name} deleted '{filename}'")
            log("FileSystem", f"Files in system: {len(self.files)}")
            return True
        return False

    def release_lock(self, pcb: PCB, detector: DeadlockDetector) -> Optional[PCB]:
        # Frees up the file system lock and cleans tracking metrics
        detector.clear(pcb.pid)
        return self.lock.release(pcb)