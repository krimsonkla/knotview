"""The backlog as a shape: what is filed under what, and how far each parent has got."""

from dataclasses import dataclass

from knotview.values.ticket import Ticket


@dataclass(frozen=True, kw_only=True)
class Branch:
    """One parent and the tickets filed under it, with what is left counted rather than guessed."""

    parent: Ticket
    children: tuple[Ticket, ...]
    terminal: tuple[str, ...]

    @property
    def done(self) -> int:
        """How many children are in a terminal status, whatever this project calls one."""
        return sum(1 for child in self.children if child.status in self.terminal)

    @property
    def total(self) -> int:
        """How many children there are."""
        return len(self.children)

    @property
    def met(self) -> int:
        """How many of the parent's own acceptance criteria are ticked."""
        return self.parent.met

    @property
    def criteria(self) -> int:
        """How many criteria the parent states, which is the figure its progress is read against."""
        return self.parent.criteria

    @property
    def complete(self) -> bool:
        """Whether every child is done, which is not the same as the parent being closed.

        Worth separating, because the gap between them is the interesting state: a parent whose
        children are all closed and which is still open is either waiting on its own criteria or
        waiting on somebody to notice.
        """
        return bool(self.children) and self.done == self.total


@dataclass(frozen=True, kw_only=True)
class Tree:
    """Every parent with its children, and the tickets belonging to nobody.

    All three parts are shown on purpose. A backlog's orphans are where work goes missing: a ticket
    filed under nothing is not visible in any epic, and a view that only drew the branches would
    leave it out of the picture entirely while looking complete. The strays are the other way work
    goes missing: filed under a parent that is closed or gone, so no live branch holds them.
    Every live ticket appears on the page exactly once.
    """

    branches: tuple[Branch, ...]
    orphans: tuple[Ticket, ...]
    strays: tuple[Ticket, ...]

    @classmethod
    def over(cls, live: tuple[Ticket, ...], *, terminal: tuple[str, ...]) -> "Tree":
        """The shape of one backlog, from the parents its tickets name."""
        held = {ticket.id: ticket for ticket in live}
        filed: dict[str, list[Ticket]] = {}
        for ticket in live:
            if ticket.parent in held:
                filed.setdefault(ticket.parent, []).append(ticket)
        branches = tuple(
            Branch(
                parent=held[parent],
                children=tuple(sorted(children, key=lambda one: (one.priority, one.id))),
                terminal=terminal,
            )
            for parent, children in sorted(
                filed.items(), key=lambda pair: (held[pair[0]].priority, pair[0])
            )
        )
        return cls(
            branches=branches,
            orphans=tuple(
                sorted(
                    (ticket for ticket in live if not ticket.parent and ticket.id not in filed),
                    key=_by_priority,
                )
            ),
            strays=tuple(
                sorted(
                    (ticket for ticket in live if ticket.parent and ticket.parent not in held),
                    key=_by_priority,
                )
            ),
        )


def _by_priority(ticket: Ticket) -> tuple[int, str]:
    """The order every list on the page uses: priority, then id for a stable tie."""
    return (ticket.priority, ticket.id)
