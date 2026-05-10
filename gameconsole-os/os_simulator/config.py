# Central config — change simulation parameters here

RAM_FRAMES = 16          # total memory frames available
TIME_QUANTUM = 3         # Round Robin time slice (ticks)
MAX_PROCESSES = 8        # maximum concurrent processes
SCHEDULER_MODE = "RR"    # "FIFO" for baseline, "RR" for enhanced
FORCE_MEMORY_EXHAUSTION = False  # set True to simulate memory full scenario