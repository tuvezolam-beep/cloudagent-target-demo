from contextlib import contextmanager
from copy import deepcopy
from threading import RLock
from typing import Iterator

from app.models import AuditEvent, Project, Task


class InMemoryStore:
    """Small thread-safe store used to keep the demo self-contained."""

    def __init__(self) -> None:
        self._lock = RLock()
        self.reset()

    def reset(self) -> None:
        with getattr(self, "_lock", RLock()):
            self.projects: dict[int, Project] = {}
            self.tasks: dict[int, Task] = {}
            self.audit_events: list[AuditEvent] = []
            self._project_sequence = 0
            self._task_sequence = 0
            self._event_sequence = 0

    def next_project_id(self) -> int:
        self._project_sequence += 1
        return self._project_sequence

    def next_task_id(self) -> int:
        self._task_sequence += 1
        return self._task_sequence

    def next_event_id(self) -> int:
        self._event_sequence += 1
        return self._event_sequence

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Rollback all in-memory changes when an operation fails."""
        with self._lock:
            snapshot = (
                deepcopy(self.projects),
                deepcopy(self.tasks),
                deepcopy(self.audit_events),
                self._project_sequence,
                self._task_sequence,
                self._event_sequence,
            )
            try:
                yield
            except Exception:
                (
                    self.projects,
                    self.tasks,
                    self.audit_events,
                    self._project_sequence,
                    self._task_sequence,
                    self._event_sequence,
                ) = snapshot
                raise


store = InMemoryStore()

