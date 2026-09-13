"""One read of a backlog, taken together so a page cannot show two different moments."""

from dataclasses import dataclass

from knotview.reading.backlog import Backlog
from knotview.values.project import Project
from knotview.values.ticket import Ticket


@dataclass(frozen=True, kw_only=True)
class Snapshot:
    """Everything one page needs, read once.

    Taken together rather than a method call per section, because a page assembled from five
    separate reads can show five different moments: an agent closing a ticket between the count and
    the list would leave a page whose total disagrees with what is under it, and the reader cannot
    see why.

    It also makes the cost obvious. One page is one snapshot, which is a handful of short processes
    over small files, and anything that wants to be cheaper can be measured against that rather than
    guessed at.
    """

    project: Project
    live: tuple[Ticket, ...]
    closed: tuple[Ticket, ...]
    ready: tuple[Ticket, ...]
    blocked: tuple[Ticket, ...]
    integrity: tuple[str, ...]

    @classmethod
    def read(cls, backlog: Backlog) -> "Snapshot":
        """One read of that backlog, in the order a page would have asked for it anyway."""
        return cls(
            project=backlog.project(),
            live=backlog.live(),
            closed=backlog.closed(),
            ready=backlog.ready(),
            blocked=backlog.blocked(),
            integrity=backlog.integrity(),
        )
