# Centralized logger — all subsystems use this, never print() directly

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()

# Tick counter — incremented by scheduler, readable by all
current_tick = 0
# Global event log for the timeline
event_log_global = []

def log(tag: str, message: str):
    # Prints a formatted log line with subsystem tag and current tick
    colors = {
        "Scheduler":   "cyan",
        "Memory":      "yellow",
        "FileSystem":  "green",
        "Concurrency": "magenta",
        "OS":          "white",
    }
    color = colors.get(tag, "white")
    console.print(f"[dim]t={current_tick:03}[/dim] [[bold {color}]{tag}[/bold {color}]] {message}")
    
    # Auto-collect major events for the timeline based on keywords
    major_keywords = [
        "created with PID", "started", "terminated", "Page fault", 
        "allocated", "wrote to", "DEADLOCK detected", "Context switch",
        "EXHAUSTION"
    ]
    if any(k in message for k in major_keywords):
        event_log_global.append((current_tick, tag, message))

def tick():
    # Increments global tick counter — call this once per scheduler tick
    global current_tick
    current_tick += 1

def section(title: str):
    # Prints a visible section divider — use between major simulation phases
    console.print(Panel(f"[bold white]{title}[/bold white]", style="dim", expand=False))

def print_process_table(processes: list):
    # Prints a rich table snapshot of all process states
    table = Table(title="Process Snapshot", box=box.SIMPLE_HEAVY)
    table.add_column("PID",       style="dim")
    table.add_column("Name",      style="cyan")
    table.add_column("State",     style="bold")
    table.add_column("Priority")
    table.add_column("Remaining", style="yellow")
    table.add_column("Frames",    style="green")

    state_colors = {
        "ready":      "blue",
        "running":    "green",
        "blocked":    "red",
        "terminated": "dim",
    }
    for p in processes:
        color = state_colors.get(p.state, "white")
        table.add_row(
            str(p.pid),
            p.name,
            f"[{color}]{p.state}[/{color}]",
            str(p.priority),
            str(p.remaining_time),
            str(len(p.memory_frames)),
        )
    console.print(table)

def print_memory_table(frames: list):
    # Prints frame allocation table — shows which process owns each frame
    table = Table(title="Memory Frame Snapshot", box=box.SIMPLE_HEAVY)
    table.add_column("Frame ID", style="dim")
    table.add_column("Occupied", style="bold")
    table.add_column("Owner PID")

    for f in frames:
        occupied = "[green]YES[/green]" if f.occupied else "[dim]no[/dim]"
        owner = str(f.owner_pid) if f.owner_pid is not None else "-"
        table.add_row(str(f.frame_id), occupied, owner)
    console.print(table)

def print_timeline(event_log: list):
    # Prints a summary timeline of major events
    table = Table(title="Simulation Timeline", box=box.SIMPLE_HEAVY)
    table.add_column("Tick",    style="dim", width=6)
    table.add_column("Tag",     style="bold", width=14)
    table.add_column("Event")

    colors = {
        "Scheduler":   "cyan",
        "Memory":      "yellow",
        "FileSystem":  "green",
        "Concurrency": "magenta",
        "OS":          "white",
    }
    for tick_n, tag, message in event_log:
        color = colors.get(tag, "white")
        table.add_row(str(tick_n), f"[{color}]{tag}[/{color}]", message)
    console.print(table)

def print_metrics_table(processes: list):
    # Prints per-process timing metrics after simulation ends
    table = Table(title="Process Metrics", box=box.SIMPLE_HEAVY)
    table.add_column("Name",        style="cyan")
    table.add_column("Burst",       style="dim")
    table.add_column("Start Tick",  style="green")
    table.add_column("End Tick",    style="green")
    table.add_column("Turnaround",  style="yellow")  # end - start
    table.add_column("Wait Time",   style="red")
    table.add_column("First Response", style="magenta")

    total_turnaround = 0
    total_wait = 0
    total_first_response = 0
    count = 0

    for p in processes:
        if p.end_tick == -1:
            continue  # skip processes that never finished
        turnaround = p.end_tick - p.start_tick
        total_turnaround += turnaround
        total_wait += p.wait_time
        if p.first_response_tick != -1:
            total_first_response += p.first_response_tick
        count += 1
        first_r = str(p.first_response_tick) if p.first_response_tick != -1 else "-"
        table.add_row(
            p.name,
            str(p.burst_time),
            str(p.start_tick),
            str(p.end_tick),
            str(turnaround),
            str(p.wait_time),
            first_r,
        )

    if count > 0:
        table.add_section()
        table.add_row(
            "[bold]Average[/bold]", "-", "-", "-",
            f"[bold yellow]{total_turnaround / count:.1f}[/bold yellow]",
            f"[bold red]{total_wait / count:.1f}[/bold red]",
            f"[bold magenta]{total_first_response / count:.1f}[/bold magenta]",
        )

    console.print(table)


def print_comparison_table(fifo_metrics: list, rr_metrics: list):
    # Side-by-side FIFO vs RR — turnaround, wait, and first response time
    table = Table(
        title="Scheduler Comparison: FIFO (Baseline) vs Round Robin (Enhanced)",
        box=box.SIMPLE_HEAVY
    )
    table.add_column("Process",          style="cyan")
    table.add_column("FIFO Turnaround",  style="dim yellow")
    table.add_column("RR Turnaround",    style="bold yellow")
    table.add_column("FIFO 1st Resp",    style="dim magenta")
    table.add_column("RR 1st Resp",      style="bold magenta")
    table.add_column("FIFO Wait",        style="dim red")
    table.add_column("RR Wait",          style="bold red")

    fifo_map = {p.name: p for p in fifo_metrics if p.end_tick != -1}
    rr_map   = {p.name: p for p in rr_metrics   if p.end_tick != -1}

    fifo_total_ta, rr_total_ta = 0, 0
    fifo_total_fr, rr_total_fr = 0, 0
    fifo_total_wt, rr_total_wt = 0, 0
    count = 0

    for name in fifo_map:
        if name not in rr_map:
            continue
        f = fifo_map[name]
        r = rr_map[name]

        f_ta = f.end_tick - f.start_tick
        r_ta = r.end_tick - r.start_tick
        f_fr = f.first_response_tick
        r_fr = r.first_response_tick
        f_wt = f.wait_time
        r_wt = r.wait_time

        fifo_total_ta += f_ta
        rr_total_ta   += r_ta
        fifo_total_fr += f_fr
        rr_total_fr   += r_fr
        fifo_total_wt += f_wt
        rr_total_wt   += r_wt
        count += 1

        # highlight RR first response in green if it beats FIFO
        rr_fr_str = f"[green]{r_fr}[/green]" if r_fr < f_fr else str(r_fr)

        table.add_row(
            name,
            str(f_ta), str(r_ta),
            str(f_fr), rr_fr_str,
            str(f_wt), str(r_wt),
        )

    if count > 0:
        table.add_section()
        avg_f_fr = fifo_total_fr / count
        avg_r_fr = rr_total_fr / count
        rr_fr_avg_str = (
            f"[bold green]{avg_r_fr:.1f}[/bold green]"
            if avg_r_fr < avg_f_fr
            else f"{avg_r_fr:.1f}"
        )
        table.add_row(
            "[bold]Average[/bold]",
            f"{fifo_total_ta/count:.1f}", f"{rr_total_ta/count:.1f}",
            f"{avg_f_fr:.1f}", rr_fr_avg_str,
            f"{fifo_total_wt/count:.1f}", f"{rr_total_wt/count:.1f}",
        )

    console.print(table)

    # Print a plain-language summary below the table
    console.print(
        "\n[dim]Note: FIFO achieves shorter turnaround for early-queued processes. "
        "RR achieves lower first response time across all processes — "
        "critical for a game console where input and audio must be responsive "
        "even while the game engine is running.[/dim]\n"
    )