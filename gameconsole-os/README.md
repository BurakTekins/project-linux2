# Game Console OS Simulator

A university project simulating core OS concepts through a game console theme.
Built in Python. Three subsystems talk to each other the way a real OS would.

## How to Run
```
uv run python main.py
```

## Project Structure
- `main.py`: Entry point, runs the simulation
- `pyproject.toml` / `uv.lock`: Dependency and environment management
- `os_simulator/`
  - `config.py`: Central configuration for the simulation parameters
  - `logger.py`: Centralized logging utility
  - `process_manager.py`: PCB, process creation, and termination
  - `scheduler.py`: Thread/process scheduling
  - `memory_manager.py`: Paging and memory bounds
  - `file_system.py`: Basic file read, write, and delete
  - `concurrency.py`: Locks and synchronization
