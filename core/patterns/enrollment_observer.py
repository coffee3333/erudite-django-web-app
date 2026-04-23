"""
Observer design pattern for enrollment notifications.

When a student is enrolled in a course (or removed), observers are notified
without the enrollment view having to know who is listening.
"""
from abc import ABC, abstractmethod
from typing import List


class EnrollmentEvent:
    """Data object carried to observers on enrollment events."""

    ENROLLED = "enrolled"
    REMOVED = "removed"

    def __init__(self, event_type: str, course, student):
        self.event_type = event_type  # 'enrolled' | 'removed'
        self.course = course
        self.student = student


class EnrollmentObserver(ABC):
    """Abstract observer — concrete observers implement on_enrollment."""

    @abstractmethod
    def on_enrollment(self, event: EnrollmentEvent) -> None:
        ...


class EnrollmentEventBus:
    """Observable: holds a list of observers and dispatches events."""

    def __init__(self):
        self._observers: List[EnrollmentObserver] = []

    def subscribe(self, observer: EnrollmentObserver) -> None:
        self._observers.append(observer)

    def unsubscribe(self, observer: EnrollmentObserver) -> None:
        self._observers.remove(observer)

    def notify(self, event: EnrollmentEvent) -> None:
        for observer in self._observers:
            try:
                observer.on_enrollment(event)
            except Exception:
                pass  # never let a failing observer break the main flow


# ── Concrete observers ────────────────────────────────────────────────────────

class EnrollmentAuditLogObserver(EnrollmentObserver):
    """Logs enrollment events to Django's logging system."""

    def on_enrollment(self, event: EnrollmentEvent) -> None:
        import logging
        logger = logging.getLogger(__name__)
        logger.info(
            "Enrollment event: student=%s course=%s action=%s",
            event.student.username,
            event.course.slug,
            event.event_type,
        )


# Singleton event bus shared across the application
enrollment_bus = EnrollmentEventBus()
enrollment_bus.subscribe(EnrollmentAuditLogObserver())
