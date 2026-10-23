"""What the first page shows: a backlog counted the ways a reader asks about it."""

from dataclasses import dataclass
from datetime import UTC, datetime

from knotview.panel.selection import FREEING, NOBODY
from knotview.panel.trend import Trend
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
class Epic:
    """A parent and how many of the children filed under it are closed.

    Counted from the live and closed lists the overview already holds, so a parent's progress
    costs no further knot read.
    """

    ticket: Ticket
    done: int
    total: int


@dataclass(frozen=True, kw_only=True)
class TagProgress:
    """A tag and how many of the tickets carrying it are closed, out of all that carry it.

    Counted over the live and closed tickets together, because that is the list its row opens:
    the tickets with the tag, closed ones included. Like a parent's progress it costs no further
    knot read.
    """

    tag: str
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
    # What the parents card shows when nothing is filed under anything: the ready queue, those
    # whose closing frees the most first, or the open tickets when nothing is ready either,
    # highest priority first.
    ready_first: tuple[Ticket, ...]
    # Where to start when the parents card leaves the ready queue unlisted: the ready tickets that
    # free the most, if any frees anything.
    start_here: tuple[Ticket, ...]
    open_first: tuple[Ticket, ...]
    ready_to_close: tuple[Ticket, ...]
    stale: tuple[Ticket, ...]
    recently_changed: tuple[Ticket, ...]
    recently_closed: tuple[Ticket, ...]
    integrity: tuple[Issue, ...]
    # The last weeks worked out from each ticket's created and closed instants; the charts that
    # draw it wait behind the charts menu like the other repeated counts.
    trend: Trend
    # Each tag with its share closed, the most open work first; behind the charts menu too.
    by_tag: tuple[TagProgress, ...]

    @classmethod
    def over(
        cls,
        snapshot: Snapshot,
        *,
        showing: int = 5,
        now: datetime | None = None,
        pinned: tuple[str, ...] = (),
    ) -> "Overview":
        """The overview of one snapshot, counted over its live tickets.

        The pinned tags are the ones the snapshot was already narrowed to, which the tag card
        leaves out: every ticket left carries them, so their rows would only repeat the totals.
        """
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
            ready_first=FREEING.ordered(snapshot.ready),
            start_here=_start_here(snapshot.ready),
            open_first=tuple(sorted(live, key=lambda t: (t.priority, t.id))),
            ready_to_close=snapshot.attention.ready_to_close,
            stale=snapshot.attention.stale,
            recently_changed=tuple(sorted(live, key=lambda t: t.updated or "", reverse=True))[
                :showing
            ],
            recently_closed=snapshot.closed[:showing],
            integrity=snapshot.integrity,
            trend=Trend.over(live, snapshot.closed, project.types, now=now or datetime.now(UTC)),
            by_tag=_by_tag(snapshot, pinned),
        )

    @property
    def live_total(self) -> int:
        """How many tickets are live, summed across statuses rather than counted a second time."""
        return sum(tally.count for tally in self.by_status)


def _start_here(ready: tuple[Ticket, ...], *, most: int = 3) -> tuple[Ticket, ...]:
    """The ready tickets tied for freeing the most other work, a few at most, or none.

    Only the ties at the top rather than the first few: a ticket that frees one beside one that
    frees seven is not where to start, and the ready queue a click away lists the rest in order.
    Nothing when no ready ticket frees anything, since a pointer to a leaf says nothing.
    """
    best = max((one.leverage or 0 for one in ready), default=0)
    if not best:
        return ()
    return tuple(one for one in FREEING.ordered(ready) if one.leverage == best)[:most]


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


def _by_tag(snapshot: Snapshot, pinned: tuple[str, ...]) -> tuple[TagProgress, ...]:
    """Every tag a ticket carries, with how many of its tickets are closed.

    Ordered by the work still open under it, most first, then by size and name, so the tags that
    need attention lead and the finished ones sink to the end. A tag the reader has pinned is left
    out, since narrowing to it already made it every ticket on the page.
    """
    left_out = set(pinned)
    done: dict[str, int] = {}
    total: dict[str, int] = {}
    for held in snapshot.live + snapshot.closed:
        for tag in set(held.tags) - left_out:
            total[tag] = total.get(tag, 0) + 1
    for held in snapshot.closed:
        for tag in set(held.tags) - left_out:
            done[tag] = done.get(tag, 0) + 1
    rows = (TagProgress(tag=tag, done=done.get(tag, 0), total=all_) for tag, all_ in total.items())
    return tuple(sorted(rows, key=lambda row: (row.done - row.total, -row.total, row.tag)))


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
