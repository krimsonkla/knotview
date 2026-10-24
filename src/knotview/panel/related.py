"""The tickets one ticket points at, each looked up in the listings so it can be drawn in full."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

from knotview.values.project import Project
from knotview.values.reference import Reference
from knotview.values.ticket import Ticket


class Pointer(Protocol):  # pylint: disable=too-few-public-methods
    """What a reference and a node of knot's dependency tree have in common: enough to look one
    up and to draw it if no listing holds it, so one lookup serves the tabs and the tree."""

    id: str
    title: str
    status: str
    missing: bool


@dataclass(frozen=True, kw_only=True)
class Relative:  # pylint: disable=too-many-instance-attributes
    """A related ticket as one tab draws it: the reference, the ticket it names, and its facts.

    The ticket is None when no listing holds the id: a reference knot reports as missing, or one
    to a ticket that went between the read of this ticket and the listings. Either is drawn from
    the reference alone, as every relation was before the listings were read.

    It holds more attributes than the linter's default allows because each is one fact a tab
    states about the ticket, and each is computed once here rather than in a template.
    """

    reference: Reference
    ticket: Ticket | None
    ready: bool = False
    # The ids it waits on that are not closed, a missing one included, since knot counts a
    # dependency on nothing as blocking and a count without it would disagree with knot's queues.
    waiting_on: tuple[str, ...] = ()
    children_closed: int = 0
    children_total: int = 0
    only_blocker: bool = False

    @property
    def status(self) -> str:
        """The status the listing states, which is newer than the reference's when they differ."""
        return self.ticket.status if self.ticket else self.reference.status


@dataclass(frozen=True, kw_only=True)
class Related:
    """Every ticket the listings hold, by id, with what knot says is ready and who is whose child.

    One value for the whole page, because each tab asks the same three questions of a different
    set of ids: what is this ticket in full, can it start, and how far along are its children. The
    listings are read whole rather than one `show` per related ticket, so an epic with forty
    children costs the page two listings, not forty processes.
    """

    project: Project
    tickets: dict[str, Ticket]
    ready_ids: frozenset[str]
    children: dict[str, tuple[Ticket, ...]]

    @classmethod
    def over(
        cls,
        project: Project,
        *,
        live: tuple[Ticket, ...],
        closed: tuple[Ticket, ...],
        ready: tuple[Ticket, ...],
    ) -> "Related":
        """The lookup over those listings, which are knot's own, never narrowed by tags."""
        everyone = (*live, *closed)
        children: dict[str, list[Ticket]] = {}
        for one in everyone:
            if one.parent:
                children.setdefault(one.parent, []).append(one)
        return cls(
            project=project,
            tickets={one.id: one for one in everyone},
            ready_ids=frozenset(one.id for one in ready),
            children={parent: tuple(held) for parent, held in children.items()},
        )

    def find(self, pointer: Pointer) -> Ticket | None:
        """The ticket that reference or tree node names, or nothing if no listing holds it."""
        return None if pointer.missing else self.tickets.get(pointer.id)

    def waiting_on(self, ticket: Ticket) -> tuple[str, ...]:
        """The ids that ticket depends on which no listing holds as closed."""
        terminal = self.project.terminal_statuses
        return tuple(
            dep
            for dep in ticket.deps
            if dep not in self.tickets or self.tickets[dep].status not in terminal
        )

    def relative(self, pointer: Pointer, *, of: str = "") -> Relative:
        """One related ticket with its facts; `of` is the ticket the page is about, when the tab
        asks whether that ticket is the last thing standing in this one's way."""
        found = self.find(pointer)
        reference = Reference(
            id=pointer.id,
            title=found.title if found else pointer.title,
            status=pointer.status,
            missing=pointer.missing,
        )
        if not found:
            return Relative(reference=reference, ticket=None)
        waiting = self.waiting_on(found)
        under = self.children.get(found.id, ())
        terminal = self.project.terminal_statuses
        return Relative(
            reference=reference,
            ticket=found,
            ready=found.id in self.ready_ids,
            waiting_on=waiting,
            children_closed=sum(1 for one in under if one.status in terminal),
            children_total=len(under),
            only_blocker=bool(of) and waiting == (of,),
        )

    def relatives(self, pointers: Iterable[Pointer], *, of: str = "") -> tuple[Relative, ...]:
        """Each of those, looked up, in the order given."""
        return tuple(self.relative(one, of=of) for one in pointers)

    def by_status(self, relatives: Iterable[Relative]) -> tuple[Relative, ...]:
        """Open work first, then by priority, then in the project's status order.

        Open means a status the project declares and does not call terminal. A status it does not
        declare goes after the closed ones and a reference to nothing goes last, as
        `Project.by_status` orders them. A ticket no listing holds has no priority to sort by, so
        it sorts after every priority within its group. The sort is stable, so knot's order is
        kept for anything still tied.
        """
        return tuple(sorted(relatives, key=self._standing))

    def by_blocking(self, relatives: Iterable[Relative]) -> tuple[Relative, ...]:
        """The tickets this one is the last open blocker of first, then the rest by status."""
        return tuple(
            sorted(relatives, key=lambda one: (not one.only_blocker, *self._standing(one)))
        )

    def tally(self, relatives: tuple[Relative, ...]) -> tuple[tuple[str, int], ...]:
        """How many of those are in each status, in the project's order, undeclared ones after.

        A reference to nothing has no status, so it is not counted; the list draws it as missing.
        """
        counts: dict[str, int] = {}
        for one in self.by_status(relatives):
            if not one.reference.missing:
                counts[one.status] = counts.get(one.status, 0) + 1
        return tuple(counts.items())

    def _standing(self, one: Relative) -> tuple[bool, int, int, int]:
        """Where a relative sorts: missing last, then open, closed, undeclared, then priority."""
        statuses = self.project.statuses
        if one.status not in statuses:
            group = 2
        else:
            group = 1 if one.status in self.project.terminal_statuses else 0
        priority = one.ticket.priority if one.ticket else self.project.priority_range[1] + 1
        rank = statuses.index(one.status) if one.status in statuses else len(statuses)
        return (one.reference.missing, group, priority, rank)
