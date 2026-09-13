"""A backlog, as the panel reads it."""

from typing import Protocol, runtime_checkable

from knotview.values.project import Project
from knotview.values.ticket import Ticket


@runtime_checkable
class Backlog(Protocol):
    """Everything the panel needs from a tracker, and nothing that writes.

    A port rather than a direct call to knot, for the reason every port here exists: the panel is
    tested against a backlog declared in a test, and a suite that needed a real project on disk for
    every assertion would be a suite nobody runs. One implementation does drive the real command,
    and it is exercised against a real project so the contract is known to hold.

    Read-only by construction. There is no method here that changes anything, which is what makes
    the panel's guarantee structural rather than a promise: the backlog stays AI-driven, and this
    watches.
    """

    def project(self) -> Project:
        """What the project says about itself: its types, statuses, modes and counts."""
        raise NotImplementedError

    def live(self) -> tuple[Ticket, ...]:
        """Every ticket that is not in a terminal status."""
        raise NotImplementedError

    def closed(self) -> tuple[Ticket, ...]:
        """Every terminal ticket, newest first, which is where the archive is read from."""
        raise NotImplementedError

    def ready(self) -> tuple[Ticket, ...]:
        """Every ticket whose blockers are all closed."""
        raise NotImplementedError

    def blocked(self) -> tuple[Ticket, ...]:
        """Every ticket with at least one open blocker."""
        raise NotImplementedError

    def ticket(self, identifier: str) -> Ticket:
        """One ticket in full: its sections, its notes and both directions of its graph."""
        raise NotImplementedError

    def integrity(self) -> tuple[str, ...]:
        """Whatever the project's own integrity check reports, as lines, empty when it is clean."""
        raise NotImplementedError

    def digest(self) -> str:
        """A value that changes when anything in the backlog does, so the page can follow it."""
        raise NotImplementedError
