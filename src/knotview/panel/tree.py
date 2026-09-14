"""The backlog as a shape: what is filed under what, to any depth, and what is filed nowhere."""

from dataclasses import dataclass

from knotview.values.ticket import Ticket


@dataclass(frozen=True, kw_only=True)
class Node:
    """One ticket and the live tickets filed under it, each of those a node of its own.

    Counts are of live children only, because that is what a listing holds: a child that closed
    is in the archive and not here. The parent's own acceptance criteria are the other progress a
    parent has, and they are counted separately since a parent can be done with its children and
    still owe its own criteria.
    """

    ticket: Ticket
    children: tuple["Node", ...]

    @property
    def total(self) -> int:
        """How many live tickets are filed directly under this one."""
        return len(self.children)

    @property
    def beneath(self) -> int:
        """How many live tickets are filed under this one at any depth."""
        return sum(1 + child.beneath for child in self.children)

    @property
    def met(self) -> int:
        """How many of this ticket's own acceptance criteria are ticked."""
        return self.ticket.met

    @property
    def criteria(self) -> int:
        """How many criteria this ticket states."""
        return self.ticket.criteria


@dataclass(frozen=True, kw_only=True)
class Tree:
    """Every parent as a nested tree, plus the tickets filed under nothing and under nothing live.

    All three parts are shown on purpose. A backlog's orphans are where work goes missing: a ticket
    filed under nothing is not visible in any epic, and a view that only drew the branches would
    leave it out of the picture entirely while looking complete. The strays are the other way work
    goes missing: filed under a parent that is closed or gone, so no live branch holds them. Every
    live ticket appears in exactly one place, under the deepest live parent that holds it.
    """

    roots: tuple[Node, ...]
    orphans: tuple[Ticket, ...]
    strays: tuple[Ticket, ...]

    @classmethod
    def over(cls, live: tuple[Ticket, ...]) -> "Tree":
        """The shape of one backlog, from the parents its tickets name."""
        held = {ticket.id: ticket for ticket in live}
        filed: dict[str, list[Ticket]] = {}
        for ticket in live:
            if ticket.parent in held:
                filed.setdefault(ticket.parent, []).append(ticket)

        def node(ticket: Ticket) -> Node:
            children = sorted(filed.get(ticket.id, ()), key=_by_priority)
            return Node(ticket=ticket, children=tuple(node(child) for child in children))

        top = [ticket for ticket in live if ticket.parent not in held]
        return cls(
            roots=tuple(node(t) for t in sorted(top, key=_by_priority) if t.id in filed),
            orphans=tuple(
                sorted((t for t in top if not t.parent and t.id not in filed), key=_by_priority)
            ),
            strays=tuple(
                sorted((t for t in top if t.parent and t.id not in filed), key=_by_priority)
            ),
        )

    def everything(self) -> tuple[Ticket, ...]:
        """Every ticket the tree holds, in page order; a test uses it to prove each shows once."""

        def walk(node: Node):
            yield node.ticket
            for child in node.children:
                yield from walk(child)

        nested = tuple(t for root in self.roots for t in walk(root))
        return nested + self.strays + self.orphans


def _by_priority(ticket: Ticket) -> tuple[int, str]:
    """The order every list on the page uses: priority, then id for a stable tie."""
    return (ticket.priority, ticket.id)
