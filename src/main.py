import copy
import random

from matplotlib import pyplot as plt

from core import Event, EventType, Job
from engine import SimulationEngine
from scheduler import FCFSScheduler, RoundRobinScheduler, SRTFScheduler
from visualize import metricsCollector, visualizer


# Generates realistic, stochastic streams of incoming jobs or network packets.
def workloadGenerator(
    num_jobs: int, max_arrival_time: int, max_burst_time: int
) -> list[Job]:
    """Generate a randomized workload for the simulation.

    Each generated job receives a unique integer ID, a random arrival time in
    the inclusive range ``[0, max_arrival_time]``, and a random burst time in
    the inclusive range ``[1, max_burst_time]``.

    Args:
        num_jobs: Number of jobs to generate.
        max_arrival_time: Maximum possible simulated arrival time.
        max_burst_time: Maximum possible CPU burst duration.

    Returns:
        List of ``Job`` instances ready to be scheduled as arrival events.
    """

    jobs = []
    for i in range(num_jobs):
        arrival_time = random.randint(0, max_arrival_time)
        total_burst_time = random.randint(1, max_burst_time)
        jobs.append(
            Job(job_id=i, arrival_time=arrival_time, total_burst_time=total_burst_time)
        )
    return jobs


# Main entry point for generating a workload and running the simulations.
if __name__ == "__main__":
    base_jobs = workloadGenerator(num_jobs=10, max_arrival_time=50, max_burst_time=100)
    schedulers = [FCFSScheduler(), RoundRobinScheduler(quantum=2.0), SRTFScheduler()]
    for job in base_jobs:
        print(job)
    print("\nStarting simulation...\n")
    for scheduler in schedulers:
        jobs_copy = copy.deepcopy(base_jobs)
        print(f"Running simulation with {scheduler.__class__.__name__}...")
        engine = SimulationEngine(scheduler=scheduler, context_switch_penalty=0.1)
        events = [Event(job.arrival_time, EventType.ARRIVAL, job) for job in jobs_copy]
        for event in events:
            engine.schedule_event(event)
        engine.run()
        metricsCollector(scheduler.__class__.__name__, engine.completed_jobs)
        visualizer(
            engine.completed_jobs,
            title=f"Execution Timeline - {scheduler.__class__.__name__}",
        )

    plt.show()  # Show the plot for all schedulers after the simulations are complete
