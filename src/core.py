from __future__ import annotations

import enum
import heapq


class EventType(enum.Enum):
    """Enumeration of all event kinds supported by the simulation engine.

    Values:
        ARRIVAL: A job has entered the simulated system and should be queued.
        COMPLETION: A running job has finished all required CPU burst time.
        QUANTUM_EXPIRATION: A Round Robin time slice has ended before completion.
    """

    ARRIVAL = "arrival"
    COMPLETION = "completion"
    QUANTUM_EXPIRATION = "quantum_expiration"


# Represents events such as job arrival, completion, and quantum expiration.
class Event:
    """Represents a timestamped event waiting to be processed.

    Events are stored in an ``EventQueue`` and ordered by timestamp so the
    simulation can advance chronologically. Each event carries an ``EventType``
    and may reference the ``Job`` affected by the event.

    Attributes:
        timestamp: Simulated time at which the event occurs.
        event_type: Type of event to process at ``timestamp``.
        job: Optional job associated with the event.
    """

    def __init__(
        self, timestamp: float, event_type: EventType, job: Job | None = None
    ) -> None:
        """Initialize an event.

        Args:
            timestamp: Simulated time at which this event should be handled.
            event_type: ``EventType`` describing the event category.
            job: Optional ``Job`` associated with the event.
        """

        self.timestamp = timestamp
        self.event_type: EventType = event_type
        self.job: Job | None = job
        self.is_cancelled: bool = False

    def __lt__(self, other: Event) -> bool:
        """Return whether this event should be ordered before another event.

        Events are primarily ordered by timestamp. When two events have the
        same timestamp, the string value of their event types is used as a
        deterministic tie breaker for heap ordering.

        Args:
            other: Another ``Event`` instance to compare against.

        Returns:
            ``True`` when this event should be processed before ``other``.
        """

        if self.timestamp == other.timestamp:
            # Tie-breaking logic: optional, but helps keep execution deterministic!
            return self.event_type.value < other.event_type.value
        return self.timestamp < other.timestamp

    def __str__(self) -> str:
        """Return a human-readable representation for logging and debugging."""

        job_id = self.job.job_id if self.job else "N/A"
        return f"Event at {self.timestamp}: {self.event_type} for Job {job_id}"


# Represents an individual process or network packet moving through the system.
class Job:
    """Represents a schedulable unit of work in the simulation.

    A job tracks arrival, execution, and completion state. The scheduler and
    engine update ``remaining_burst_time``, ``start_time``, and
    ``completion_time`` as the simulation progresses.

    Attributes:
        job_id: Unique identifier used for reporting and plotting.
        arrival_time: Simulated time when the job becomes available.
        total_burst_time: Total CPU time required to complete the job.
        remaining_burst_time: CPU time still required before completion.
        start_time: First simulated time at which the job receives CPU time.
        completion_time: Simulated time at which the job finishes.
    """

    def __init__(
        self, job_id: int, arrival_time: float, total_burst_time: float
    ) -> None:
        """Initialize a job with arrival and burst-time information.

        Args:
            job_id: Unique identifier for the job.
            arrival_time: Simulated time when the job enters the system.
            total_burst_time: Total CPU burst duration required by the job.
        """

        self.job_id = job_id
        self.arrival_time = arrival_time
        self.total_burst_time = total_burst_time
        self.remaining_burst_time = total_burst_time
        self.start_time: float | None = None
        self.completion_time: float | None = None
        self.execution_intervals: list[tuple[float, float]] = []

    def turnaround_time(self) -> float | None:
        """Calculate the elapsed time from arrival to completion.

        Returns:
            The turnaround time when the job has completed; otherwise ``None``.
        """

        return (
            self.completion_time - self.arrival_time
            if self.completion_time is not None
            else None
        )

    def waiting_time(self) -> float | None:
        """Calculate total time spent waiting outside CPU execution.

        Returns:
            Turnaround time minus required CPU burst time when complete;
            otherwise ``None``.
        """

        turnaround_time = self.turnaround_time()
        return (
            turnaround_time - self.total_burst_time
            if turnaround_time is not None
            else None
        )

    def response_time(self) -> float | None:
        """Calculate the delay between arrival and first CPU service.

        Returns:
            The response time once the job has started; otherwise ``None``.
        """

        return (
            self.start_time - self.arrival_time if self.start_time is not None else None
        )

    def __str__(self) -> str:
        """Return a compact human-readable summary of the job."""

        return (
            f"Job {self.job_id}: Arrived at {self.arrival_time}, "
            f"Total Burst Time: {self.total_burst_time}"
        )


# Represents a queue of events that need to be processed in chronological order.
class EventQueue:
    """Priority queue for simulation events.

    The queue uses Python's ``heapq`` module to keep events ordered by their
    ``Event.__lt__`` comparison. Popping from the queue always returns the next
    chronological event available to the simulation engine.

    Attributes:
        events: Internal heap-backed list of pending ``Event`` objects.
    """

    def __init__(self) -> None:
        """Create an empty event queue."""

        self.events: list[Event] = []

    def add_event(self, event: Event) -> None:
        """Insert an event into the queue.

        Args:
            event: ``Event`` instance to schedule for future processing.
        """

        # Automatically places the event in min-heap order in O(log N)
        heapq.heappush(self.events, event)

    def pop_event(self) -> Event | None:
        """Remove and return the next event in chronological order.

        Returns:
            The next ``Event`` when one exists; otherwise ``None``.
        """

        return heapq.heappop(self.events) if self.events else None

    def is_empty(self) -> bool:
        """Return whether the queue has no pending events."""

        return len(self.events) == 0

    def __len__(self) -> int:
        """Return the number of pending events in the queue."""

        return len(self.events)
