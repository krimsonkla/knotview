"""What the first page shows: a backlog counted the ways a reader asks about it."""

from dataclasses import dataclass

from knotview.reading.snapshot import Snapshot
from knotview.values.ticket import Ticket


@dataclass(frozen=True, kw_only=True)
class Tally:
    """One row of a count: what it is, how many, and which filter narrows to it."""

    label: str
    count: int
    filter: str
    value: str


@dataclass(frozen=True, kw_only=True)
class Overview:
    """The backlog counted by type, by status and by priority, plus the queues and the parents.

    Counted from the project's own declared values rather than from whatever the tickets happen to
    use, and that is the difference that matters. A type nobody has filed yet appears with a count
    of zero, which tells a reader the type exists; counting only where a value occurs would make it
    vanish and read as though the project did not have one.

    The queues are knot's own: ready means every blocker closed, blocked means at least one open.
    They are counted here rather than listed, because the first page is a map and the lists are one
    click away.
    """

    by_type: tuple[Tally, ...]
    by_status: tuple[Tally, ...]
    by_priority: tuple[Tally, ...]
    by_queue: tuple[Tally, ...]
    parents: tuple[Ticket, ...]
    recently_closed: tuple[Ticket, ...]
    integrity: tuple[str, ...]

    @classmethod
    def over(cls, snapshot: Snapshot, *, showing: int = 8) -> "Overview":
        """The overview of one snapshot, counted over its live tickets."""
        project, live = snapshot.project, snapshot.live
        return cls(
            by_type=tuple(
                Tally(
                    label=kind,
                    count=sum(1 for held in live if held.type == kind),
                    filter="type",
                    value=kind,
                )
                for kind in project.types
            ),
            by_status=tuple(
                Tally(
                    label=status,
                    count=sum(1 for held in live if held.status == status),
                    filter="status",
                    value=status,
                )
                for status in project.open_statuses
            ),
            by_priority=tuple(
                Tally(
                    label=f"p{priority}",
                    count=sum(1 for held in live if held.priority == priority),
                    filter="priority",
                    value=str(priority),
                )
                for priority in project.priorities
            ),
            by_queue=(
                Tally(label="ready", count=len(snapshot.ready), filter="queue", value="ready"),
                Tally(
                    label="blocked", count=len(snapshot.blocked), filter="queue", value="blocked"
                ),
                Tally(
                    label="unassigned",
                    count=sum(1 for held in live if not held.assignee),
                    filter="assignee",
                    value="",
                ),
            ),
            parents=_parents(live),
            recently_closed=snapshot.closed[:showing],
            integrity=snapshot.integrity,
        )

    @property
    def live_total(self) -> int:
        """How many tickets are live, summed across statuses rather than counted a second time."""
        return sum(tally.count for tally in self.by_status)


def _parents(live: tuple[Ticket, ...]) -> tuple[Ticket, ...]:
    """Every ticket something else is filed under, by priority then id.

    Read from the children's parents rather than from a type called epic, because what makes a
    ticket a parent is that something points at it. A project whose types do not include an epic
    still has this shape, and a panel looking for the word would show it nothing.
    """
    named = {held.parent for held in live if held.parent}
    return tuple(
        sorted(
            (held for held in live if held.id in named),
            key=lambda held: (held.priority, held.id),
        )
    )
