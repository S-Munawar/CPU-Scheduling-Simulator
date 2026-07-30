from core import Event, EventQueue, EventType, Job
from scheduler import RoundRobinScheduler, Scheduler, SRTFScheduler


class CPUCore:
    """Models the single CPU resource used by the simulation.

    The core can execute at most one job at a time. It also stores the context
    switch penalty that is added to each scheduled execution interval.

    Attributes:
        current_job: Job currently assigned to the CPU, or ``None`` when idle.
        context_switch_penalty: Extra simulated time added when a job runs.
    """

    def __init__(self, context_switch_penalty: float) -> None:
        """Initialize an idle CPU core.

        Args:
            context_switch_penalty: Simulated overhead added to each execution
                interval scheduled by the engine.
        """

        self.current_job: Job | None = None
        self.context_switch_penalty = context_switch_penalty
        self.last_start_time: float = 0.0
        self.active_event: Event | None = None  # Track event to cancel on preemption

    def is_idle(self) -> bool:
        """Return whether the CPU currently has no assigned job."""

        return self.current_job is None

    def assign_job(self, job: Job, start_time: float, active_event: Event) -> None:
        """Assign a job to the CPU for execution.

        Args:
            job: Job selected by the scheduler to run next.
            start_time: Time at which the job starts executing.
            active_event: Event associated with the job's execution.
        """

        self.current_job = job
        self.last_start_time = start_time
        self.active_event = active_event

    def release(self) -> None:
        """Mark the CPU as idle by clearing the current job reference."""

        self.current_job = None
        self.active_event = None


class SimulationEngine:
    """Coordinates event processing, scheduling, and CPU execution.

    The engine advances a simulated clock by repeatedly popping events from the
    event queue. Arrival events place jobs into the scheduler, completion events
    record finished jobs, and Round Robin quantum-expiration events requeue
    unfinished work.

    Attributes:
        clock: Current simulated time.
        event_queue: Priority queue of future events.
        scheduler: Scheduling policy used to choose the next job.
        jobs: Optional list for storing known jobs.
        cpu: Single simulated CPU core.
        completed_jobs: Jobs that have finished execution.
    """

    def __init__(
        self, scheduler: Scheduler, context_switch_penalty: float = 0.0
    ) -> None:
        """Initialize the engine with a scheduler and CPU timing overhead.

        Args:
            scheduler: Scheduler implementation that owns the ready queue.
            context_switch_penalty: Extra simulated time added to each CPU
                execution interval.
        """

        self.clock = 0.0
        self.event_queue = EventQueue()
        self.scheduler = scheduler
        self.jobs: list[Job] = []
        self.cpu = CPUCore(context_switch_penalty=context_switch_penalty)
        self.completed_jobs: list[Job] = []

    def schedule_event(self, event: Event) -> None:
        """Schedule an event for future processing.

        Args:
            event: Event to insert into the engine's event queue.
        """

        self.event_queue.add_event(event)

    def run(self) -> None:
        """Run the simulation until no future events remain.

        The method mutates scheduler queues, CPU state, job timing fields, and
        ``completed_jobs``. It also prints each processed event to standard
        output for traceability.
        """

        while not self.event_queue.is_empty():
            event = self.event_queue.pop_event()
            if event is None:
                break

            # Skip events cancelled by preemption
            if getattr(event, "is_cancelled", False):
                continue

            self.clock = event.timestamp

            # Handle the event based on its type
            if event.event_type == EventType.ARRIVAL:
                if event.job is None:
                    raise ValueError("Arrival events must include a job.")
                self.scheduler.add_job(event.job)

                # Check for Preemption if SRTF is active
                if isinstance(self.scheduler, SRTFScheduler) and not self.cpu.is_idle():
                    running_job = self.cpu.current_job
                    if running_job is None:
                        raise RuntimeError("CPU cannot be busy without a current job.")

                    # Update running job's remaining time up to current clock
                    elapsed_time = max(0.0, self.clock - self.cpu.last_start_time)
                    executed_time = min(elapsed_time, running_job.remaining_burst_time)
                    current_remaining_time = (
                        running_job.remaining_burst_time - executed_time
                    )
                    running_job.remaining_burst_time = current_remaining_time
                    self.cpu.last_start_time = self.clock

                    if current_remaining_time > 0:
                        # Fetch shortest job from scheduler (includes the new arrival)
                        shortest_job = self.scheduler.get_next_job()

                        if (
                            shortest_job
                            and shortest_job.remaining_burst_time
                            < current_remaining_time
                        ):
                            running_job.execution_intervals.append(
                                (self.cpu.last_start_time, self.clock)
                            )
                            # PREEMPTION TRIGGERED!
                            if self.cpu.active_event:
                                self.cpu.active_event.is_cancelled = True

                            # Requeue both jobs back into min-heap
                            self.scheduler.add_job(running_job)
                            self.scheduler.add_job(shortest_job)
                            self.cpu.release()
                        else:
                            # Put shortest_job back if it wasn't strictly shorter
                            if shortest_job:
                                self.scheduler.add_job(shortest_job)

            elif event.event_type == EventType.QUANTUM_EXPIRATION:
                if event.job is None:
                    raise ValueError("Quantum expiration events must include a job.")
                if not isinstance(self.scheduler, RoundRobinScheduler):
                    raise TypeError(
                        "Quantum expiration events require a Round Robin scheduler."
                    )
                event.job.remaining_burst_time -= self.scheduler.quantum
                event.job.execution_intervals.append(
                    (self.cpu.last_start_time, self.clock)
                )
                self.cpu.release()
                self.scheduler.add_job(event.job)

            else:
                if event.job is None:
                    raise ValueError("Completion events must include a job.")
                event.job.remaining_burst_time = 0.0
                event.job.completion_time = self.clock
                event.job.execution_intervals.append(
                    (self.cpu.last_start_time, self.clock)
                )
                self.completed_jobs.append(event.job)
                self.cpu.release()

            # If the CPU is idle, fetch the next job from the scheduler
            if self.cpu.is_idle() and not self.scheduler.is_empty():
                next_job = self.scheduler.get_next_job()
                if next_job is None:
                    continue

                if next_job.start_time is None:
                    next_job.start_time = self.clock

                # Schedule the next event based on the job's remaining burst time
                if isinstance(self.scheduler, RoundRobinScheduler):
                    execution_time = min(
                        next_job.remaining_burst_time, self.scheduler.quantum
                    )
                else:
                    execution_time = next_job.remaining_burst_time

                finish_time = (
                    self.clock + execution_time + self.cpu.context_switch_penalty
                )

                # Create event and bind to CPU state
                event_type = (
                    EventType.QUANTUM_EXPIRATION
                    if execution_time < next_job.remaining_burst_time
                    else EventType.COMPLETION
                )

                future_event = Event(finish_time, event_type, next_job)
                self.cpu.assign_job(
                    next_job, start_time=self.clock, active_event=future_event
                )
                self.schedule_event(future_event)
