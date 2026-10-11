"""What the first page shows: a backlog counted the ways a reader asks about it."""

from dataclasses import dataclass

from knotview.panel.selection import NOBODY
from knotview.panel.tree import Tree
from knotview.reading.snapshot import Snapshot
from knotview.values.ticket import Ticket
from knotview.values.issue import Issue


@dataclass(frozen=True, kw_only=True)
class Tally:
    """One row of a count: what it is, how many, and which filter narrows to it."""

    label: str
    count: int
    filter: str
    value: str


@dataclass(frozen=True, kw_only=True)
class Progress:
    """How far one parent has got: its own criteria, and the live children still under it."""

    ticket: Ticket
    met: int
    criteria: int
    children: int

    @property
    def remaining(self) -> int:
        """Criteria still unticked, which is what the card is sorted by."""
        return self.criteria - self.met


@dataclass(frozen=True, kw_only=True)
class Epic:
    """A parent and how many of the children filed under it are closed.

    Counted from the live and closed lists the overview already holds, so a parent's progress
    costs no further knot read.
    """

    ticket: Ticket
    done: int
    total: int


@dataclass(frozen=True, kw_only=True)
class Overview:  # pylint: disable=too-many-instance-attributes
    """The backlog counted by type, by status and by priority, plus the queues and the parents.

    Counted from the project's own declared values rather than from whatever the tickets happen to
    use, and that is the difference that matters. A type nobody has filed yet appears with a count
    of zero, which tells a reader the type exists; counting only where a value occurs would make it
    vanish and read as though the project did not have one.

    The queues are knot's own: ready means every blocker closed, blocked means at least one open.
    They are counted here rather than listed, because the first page is a map and the lists are one
    click away.

    The documents card is the one exception to keeping zeros, and only as a whole: within the card
    every declared type keeps its row, zero or not, but the card goes when no ticket it counts owns
    a document, since a card of zeros there says nothing a project without documents needs. It
    counts tickets owning each type, not documents, because knot's listings name a ticket's types
    without counting them, and the count then equals the list its row links to.

    It holds one attribute per card the page draws, which is more than the linter's default;
    splitting them would only move the page's shape out of the one value that describes it.
    """

    by_type: tuple[Tally, ...]
    by_status: tuple[Tally, ...]
    by_priority: tuple[Tally, ...]
    by_queue: tuple[Tally, ...]
    by_document: tuple[Tally, ...]
    # The terminal statuses counted from the snapshot's closed tickets rather than from knot's raw
    # archive count, so they narrow with everything else when the reader has chosen tags, and
    # each links to its own list the way the open statuses do.
    by_terminal: tuple[Tally, ...]
    parents: tuple[Ticket, ...]
    epics: tuple[Epic, ...]
    # What the parents are called, from the types the project declares, so a project whose
    # parents are all epics reads "epics" and one with none of that type never sees the word.
    parents_label: str
    # What the parents card shows when nothing is filed under anything: the ready queue, or the
    # open tickets when nothing is ready either, highest priority first.
    ready_first: tuple[Ticket, ...]
    open_first: tuple[Ticket, ...]
    progress: tuple[Progress, ...]
    ready_to_close: tuple[Ticket, ...]
    stale: tuple[Ticket, ...]
    recently_changed: tuple[Ticket, ...]
    recently_closed: tuple[Ticket, ...]
    integrity: tuple[Issue, ...]

    @classmethod
    def over(cls, snapshot: Snapshot, *, showing: int = 5) -> "Overview":
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
                    value=NOBODY,
                ),
            ),
            by_document=_by_document(snapshot),
            by_terminal=tuple(
                Tally(
                    label=status,
                    count=sum(1 for held in snapshot.closed if held.status == status),
                    filter="status",
                    value=status,
                )
                for status in project.terminal_statuses
            ),
            parents=_parents(live),
            epics=_epics(_parents(live), snapshot),
            parents_label=_named(_parents(live), project.types),
            ready_first=tuple(sorted(snapshot.ready, key=lambda t: (t.priority, t.id))),
            open_first=tuple(sorted(live, key=lambda t: (t.priority, t.id))),
            progress=_progress(live),
            ready_to_close=snapshot.attention.ready_to_close,
            stale=snapshot.attention.stale,
            recently_changed=tuple(sorted(live, key=lambda t: t.updated or "", reverse=True))[
                :showing
            ],
            recently_closed=snapshot.closed[:showing],
            integrity=snapshot.integrity,
        )

    @property
    def live_total(self) -> int:
        """How many tickets are live, summed across statuses rather than counted a second time."""
        return sum(tally.count for tally in self.by_status)


def _by_document(snapshot: Snapshot) -> tuple[Tally, ...]:
    """Live tickets owning each declared document type, or nothing when none owns any."""
    project = snapshot.project
    owned = [set(project.types_of(held)) for held in snapshot.live]
    tallies = tuple(
        Tally(
            label=kind, count=sum(1 for types in owned if kind in types), filter="doc", value=kind
        )
        for kind in project.doc_types
    )
    return tallies if any(tally.count for tally in tallies) else ()


def _progress(live: tuple[Ticket, ...]) -> tuple[Progress, ...]:
    """Every parent that states criteria, nearest to done first, with its live children counted."""
    roots = Tree.over(live).roots
    stated = [
        Progress(ticket=r.ticket, met=r.met, criteria=r.criteria, children=r.beneath)
        for r in roots
        if r.criteria
    ]
    return tuple(sorted(stated, key=lambda p: (p.remaining, p.ticket.priority, p.ticket.id)))


def _named(parents: tuple[Ticket, ...], types: tuple[str, ...]) -> str:
    """The parents named by their declared types, in the project's order, as plurals.

    knot declares no type for a parent: a parent is whatever something else names, so the label
    comes from the types the parents actually have rather than from a word chosen here.
    """
    held = {one.type for one in parents}
    kinds = [_plural(kind) for kind in types if kind in held]
    if not kinds:
        return "parents"
    return kinds[0] if len(kinds) == 1 else ", ".join(kinds[:-1]) + " and " + kinds[-1]


def _plural(word: str) -> str:
    """An English plural good enough for a ticket type's name."""
    if word.endswith(("s", "x", "z", "ch", "sh")):
        return word + "es"
    if word.endswith("y") and word[-2:-1] not in "aeiou":
        return word[:-1] + "ies"
    return word + "s"


def _epics(parents: tuple[Ticket, ...], snapshot: Snapshot) -> tuple[Epic, ...]:
    """Each parent with the share of its children that are closed."""
    return tuple(
        Epic(
            ticket=parent,
            done=sum(1 for one in snapshot.closed if one.parent == parent.id),
            total=sum(1 for one in snapshot.live + snapshot.closed if one.parent == parent.id),
        )
        for parent in parents
    )


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
