# Handles paging, page faults, and the memory pool

from dataclasses import dataclass
from typing import Optional
from os_simulator.process_manager import PCB
from os_simulator.logger import log
from os_simulator import config

@dataclass
class Frame:
    frame_id: int
    occupied: bool
    owner_pid: Optional[int]

class MemoryManager:
    # Chosen: Fixed-size frame allocation (Paging).
    # Alternative considered: Variable-sized contiguous allocation (Segmentation).
    # Rejected because: Paging prevents external fragmentation, which is crucial for limited console memory.
    # Trade-off accepted: Internal fragmentation if processes don't utilize their entire frame.
    def __init__(self):
        # Initializes RAM_FRAMES frames, all unoccupied
        self.frames = [Frame(frame_id=i, occupied=False, owner_pid=None) for i in range(config.RAM_FRAMES)]

    def allocate(self, pcb: PCB, num_frames: int) -> bool:
        # Tries to allocate num_frames to the process
        if getattr(config, "FORCE_MEMORY_EXHAUSTION", False):
            log("Memory", f"Page fault — {pcb.name} requested {num_frames} frames, only 0 available")
            return False

        free_frames = [f for f in self.frames if not f.occupied]
        
        if len(free_frames) >= num_frames:
            allocated = free_frames[:num_frames]
            for frame in allocated:
                frame.occupied = True
                frame.owner_pid = pcb.pid
            pcb.memory_frames = [f.frame_id for f in allocated]
            log("Memory", f"{pcb.name} allocated {num_frames} frames: {pcb.memory_frames}")
            new_free = sum(1 for f in self.frames if not f.occupied)
            log("Memory", f"Free frames after allocation: {new_free} / {config.RAM_FRAMES}")
            return True
        else:
            log("Memory", f"Page fault — {pcb.name} requested {num_frames} frames, only {len(free_frames)} available")
            return False

    def deallocate(self, pcb: PCB):
        # Frees all frames owned by this process
        num_frames = len(pcb.memory_frames)
        for frame_id in pcb.memory_frames:
            self.frames[frame_id].occupied = False
            self.frames[frame_id].owner_pid = None
        pcb.memory_frames.clear()
        log("Memory", f"{pcb.name} released {num_frames} frames")
        new_free = sum(1 for f in self.frames if not f.occupied)
        log("Memory", f"Free frames after deallocation: {new_free} / {config.RAM_FRAMES}")

    def translate_address(self, pcb: PCB, logical_address: int) -> Optional[int]:
        # Simulates address translation: logical -> physical
        if 0 <= logical_address < len(pcb.memory_frames):
            physical_address = pcb.memory_frames[logical_address]
            log("Memory", f"{pcb.name} address {logical_address} -> frame {physical_address}")
            return physical_address
        return None

    def is_memory_full(self) -> bool:
        # Returns True if zero free frames remain
        return all(f.occupied for f in self.frames)

    def status(self):
        # Logs a summary: total frames, used, free
        total = len(self.frames)
        used = sum(1 for f in self.frames if f.occupied)
        free = total - used
        log("Memory", f"Status — total: {total} | used: {used} | free: {free}")

    def handle_exhaustion(self, pcb: PCB, scheduler, process_manager):
        # Called when allocating memory fails for a process
        log("Memory", f"EXHAUSTION — no free frames left, {pcb.name} cannot run")
        log("Memory", f"{pcb.name} suspended until memory is available")
        scheduler.handle_blocked(pcb, "memory exhaustion", process_manager)
