import heapq
from abc import ABC, abstractmethod
from collections import deque

from core import Job

# These classes handle the algorithm logic (how jobs are selected for execution).


# Defines the standard interface for all CPU scheduling algorithms.
class Scheduler(ABC):
    """Abstract interface for CPU scheduling algorithms.

    Concrete schedulers own a ready queue and implement the policy for
    accepting jobs, selecting the next job, and reporting whether work remains.
    The simulation engine depends only on this interface.
    """

    @abstractmethod
    def add_job(self, job: Job) -> None:
        """Add a job to the scheduler's ready queue.

        Args:
            job: Job that has arrived or has been preempted and should wait for
                future CPU time.
        """

        pass

    @abstractmethod
    def get_next_job(self) -> Job | None:
        """Fetch and remove the next job selected for execution.

        Returns:
            The next ``Job`` according to the scheduler policy, or ``None`` if
            no job is available.
        """

        pass

    @abstractmethod
    def is_empty(self) -> bool:
        """Return whether the scheduler has no ready jobs."""

        pass


class FCFSScheduler(Scheduler):
    """First-Come, First-Served scheduler implementation.

    Jobs are executed in the order they enter the ready queue. This
    non-preemptive policy uses a FIFO ``deque`` for efficient append and pop
    operations.
    """

    def __init__(self) -> None:
        """Initialize an empty FIFO ready queue."""

        self.ready_queue: deque[Job] = deque()

    def add_job(self, job: Job) -> None:
        """Append a job to the back of the FIFO ready queue.

        Args:
            job: Job that should wait for CPU execution.
        """

        self.ready_queue.append(job)

    def get_next_job(self) -> Job | None:
        """Remove and return the oldest ready job.

        Returns:
            The job at the front of the ready queue, or ``None`` if the queue is
            empty.
        """

        if self.ready_queue:
            return self.ready_queue.popleft()
        return None

    def is_empty(self) -> bool:
        """Return whether the FIFO ready queue contains no jobs."""

        return len(self.ready_queue) == 0


class RoundRobinScheduler(Scheduler):
    """Round Robin scheduler implementation.

    Jobs are stored in FIFO order and the engine enforces the configured
    ``quantum`` by requeuing unfinished jobs after each time slice expires.

    Attributes:
        ready_queue: Queue of jobs waiting for their next CPU time slice.
        quantum: Maximum simulated CPU time granted per dispatch.
    """

    def __init__(self, quantum: float) -> None:
        """Initialize an empty ready queue with a fixed time quantum.

        Args:
            quantum: Maximum amount of simulated CPU time a job receives before
                preemption.
        """

        self.ready_queue: deque[Job] = deque()
        self.quantum = quantum

    def add_job(self, job: Job) -> None:
        """Append a job to the back of the Round Robin queue.

        Args:
            job: Newly arrived or preempted job waiting for a time slice.
        """

        self.ready_queue.append(job)

    def get_next_job(self) -> Job | None:
        """Remove and return the next job eligible for a time slice.

        Returns:
            The next queued job, or ``None`` if no jobs are ready.
        """

        if self.ready_queue:
            return self.ready_queue.popleft()
        return None

    def is_empty(self) -> bool:
        """Return whether the Round Robin ready queue contains no jobs."""

        return len(self.ready_queue) == 0


class SRTFScheduler(Scheduler):
    """Shortest-Remaining-Time-First scheduler placeholder.

    The current implementation stores jobs in arrival order using a ``deque``.
    It satisfies the scheduler interface, but it does not yet reorder jobs by
    remaining burst time.
    """

    def __init__(self) -> None:
        """Initialize an empty ready queue for SRTF scheduling."""

        self.ready_queue: list[tuple[float, int, Job]] = []

    def add_job(self, job: Job) -> None:
        """Append a job to the ready queue.

        Args:
            job: Job waiting for future CPU execution.
        """
        entry = (job.remaining_burst_time, job.job_id, job)
        heapq.heappush(self.ready_queue, entry)

    def get_next_job(self) -> Job | None:
        """Remove and return the next queued job.

        Returns:
            The next job in queue order, or ``None`` if the queue is empty.
        """

        if self.ready_queue:
            return heapq.heappop(self.ready_queue)[2]
        return None

    def is_empty(self) -> bool:
        """Return whether the ready queue has no jobs."""

        return len(self.ready_queue) == 0
