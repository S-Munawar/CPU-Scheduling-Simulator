# CPU Scheduling Simulator

A discrete-event simulator for comparing CPU scheduling algorithms. The
project generates a randomized workload, runs it through multiple schedulers,
prints performance metrics, and displays execution timelines with Matplotlib.

## Features

- First-Come, First-Served (FCFS) scheduling
- Round Robin scheduling with configurable quantum
- Event-driven simulation for arrivals, completions, and time-slice expiration
- Metrics for turnaround time, waiting time, and CPU utilization
- Gantt-style timeline visualization for completed jobs

## Project Layout

```text
src/
  core.py        Event, event queue, and job models
  scheduler.py   Scheduler interface and scheduling algorithms
  engine.py      Simulation engine and CPU core model
  visualize.py   Metrics and timeline plotting
  main.py        Example simulation entry point
```

## Requirements

- Python 3.13
- Matplotlib
- pytest
- mypy
- Ruff
- pre-commit

Install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python src/main.py
```

The default run generates 10 random jobs, compares FCFS and Round Robin, prints
metrics for each scheduler, and opens timeline plots.

## Development Checks

Run the formatter/linter checks:

```bash
ruff check .
```

Run static type checks:

```bash
mypy .
```

Run tests:

```bash
pytest
```

Install pre-commit hooks:

```bash
pre-commit install
```

## Notes

The current `SRTFScheduler` class is a placeholder that satisfies the scheduler
interface but does not yet reorder jobs by shortest remaining time.
