import matplotlib.pyplot as plt

from core import Job


def metricsCollector(algorithm_name: str, completed_jobs: list[Job]) -> None:
    """Print aggregate performance metrics for completed jobs.

    The metrics include average turnaround time, average waiting time, and CPU
    utilization based on total burst time divided by the latest completion time.
    If no jobs completed, the function prints a short message and returns.

    Args:
        algorithm_name: Name of the scheduler or algorithm being reported.
        completed_jobs: Jobs that finished during a simulation run.
    """

    if not completed_jobs:
        print("No completed jobs to analyze.")
        return

    turnaround_times: list[float] = []
    waiting_times: list[float] = []
    completion_times: list[float] = []

    for job in completed_jobs:
        turnaround_time = job.turnaround_time()
        waiting_time = job.waiting_time()
        if (
            turnaround_time is None
            or waiting_time is None
            or job.completion_time is None
        ):
            raise ValueError("Completed jobs must include all timing metrics.")

        turnaround_times.append(turnaround_time)
        waiting_times.append(waiting_time)
        completion_times.append(job.completion_time)

    total_turnaround = sum(turnaround_times)
    total_waiting = sum(waiting_times)
    total_burst = sum(j.total_burst_time for j in completed_jobs)

    max_completion = max(completion_times)
    num_jobs = len(completed_jobs)

    avg_turnaround = total_turnaround / num_jobs
    avg_waiting = total_waiting / num_jobs
    cpu_utilization = (
        (total_burst / max_completion) * 100 if max_completion > 0 else 0.0
    )

    print(f"\n================ {algorithm_name} METRICS SUMMARY ================")
    print(f"Total Jobs Processed : {num_jobs}")
    print(f"Average Turnaround   : {avg_turnaround:.2f} units")
    print(f"Average Wait Time    : {avg_waiting:.2f} units")
    print(f"CPU Utilization      : {cpu_utilization:.2f}%")
    print("=================================================================\n")


def visualizer(
    completed_jobs: list[Job], title: str = "CPU Execution Timeline"
) -> None:
    """Plot a Gantt chart showing completed job execution windows.

    Jobs are sorted by ID for a stable Y-axis. Each horizontal bar begins at the
    job's recorded ``start_time`` and spans until ``completion_time``.

    Args:
        completed_jobs: Completed jobs with populated timing fields.
        title: Title displayed above the chart.
    """

    FIGURE_SIZE = (10, 6)
    BAR_COLOR = "skyblue"
    EDGE_COLOR = "black"

    fig, ax = plt.subplots(figsize=FIGURE_SIZE)

    # Sort jobs by job_id for clean Y-axis display
    sorted_jobs = sorted(completed_jobs, key=lambda j: j.job_id)
    for job in sorted_jobs:
        if job.start_time is None or job.completion_time is None:
            raise ValueError("Completed jobs must include start and completion times.")

        # Plot horizontal execution bar from start_time to completion_time
        duration = job.completion_time - job.start_time
        ax.barh(
            job.job_id,
            duration,
            left=job.start_time,
            color=BAR_COLOR,
            edgecolor=EDGE_COLOR,
        )

    ax.set_xlabel("Time")
    ax.set_ylabel("Job ID")
    ax.set_yticks(
        [job.job_id for job in sorted_jobs],
        [f"Job {job.job_id}" for job in sorted_jobs],
    )
    ax.set_title(title)
    ax.grid(axis="x")
    plt.tight_layout()
