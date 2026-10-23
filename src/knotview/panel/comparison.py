"""Two worktrees' backlogs side by side: what one holds that the other does not, and what moved."""

from dataclasses import dataclass
from itertools import chain

from knotview.values.ticket import Ticket

# The fields a reader compares two copies of a ticket by, in the order a row states them. Each is
# one a branch changes on purpose: a move, a re-prioritisation, a retitle or a retype. Times are
# left out, since every edit moves them and a list of tickets whose time moved is a list of
# everything touched, which says less than the fields that did change.
FIELDS = ("status", "priority", "title", "type")


@dataclass(frozen=True, kw_only=True)
class Change:
    """One field that reads differently in the two worktrees, with both values as written."""

    field: str
    here: str
    there: str


@dataclass(frozen=True, kw_only=True)
class Pair:
    """One ticket both worktrees hold, each copy as its own worktree reads it."""

    here: Ticket
    there: Ticket
    changes: tuple[Change, ...]

    @property
    def id(self) -> str:
        """The id both copies share."""
        return self.here.id


@dataclass(frozen=True, kw_only=True)
class Comparison:
    """The chosen worktree's backlog against another's, in the groups a reader merging looks for.

    A ticket is in exactly one group. Closed on one side and live on the other is its own group
    rather than one more changed status, because it is the difference a merge decides: work one
    branch finished that the other still has open. Tickets that read the same on both sides are
    kept by id only, so the page can count them without listing a backlog the reader already has.
    """

    only_here: tuple[Ticket, ...]
    only_there: tuple[Ticket, ...]
    parted: tuple[Pair, ...]
    changed: tuple[Pair, ...]
    alike: tuple[str, ...]

    @classmethod
    def between(
        cls,
        *,
        here: tuple[tuple[Ticket, ...], tuple[Ticket, ...]],
        there: tuple[tuple[Ticket, ...], tuple[Ticket, ...]],
    ) -> "Comparison":
        """Two backlogs, each given as its live tickets and its closed tickets.

        Closed means listed by knot as closed, rather than a status this compares against the
        project's terminal statuses, so the two worktrees may even configure them differently.
        """
        ours = _by_id(here)
        theirs = _by_id(there)
        parted: list[Pair] = []
        changed: list[Pair] = []
        alike: list[str] = []
        for identifier, (mine, closed) in ours.items():
            if identifier not in theirs:
                continue
            other, other_closed = theirs[identifier]
            pair = Pair(here=mine, there=other, changes=_changes(mine, other))
            if closed != other_closed:
                parted.append(pair)
            elif pair.changes:
                changed.append(pair)
            else:
                alike.append(identifier)
        return cls(
            only_here=tuple(one for one, _ in ours.values() if one.id not in theirs),
            only_there=tuple(one for one, _ in theirs.values() if one.id not in ours),
            parted=tuple(parted),
            changed=tuple(changed),
            alike=tuple(alike),
        )

    def within(self, kept: set[str]) -> "Comparison":
        """Only the tickets whose id is kept, which is how the reader's pinned tags narrow it.

        By id rather than by tags, so a ticket that gained a pinned tag on one side still shows
        as changed instead of vanishing from one side and reading as only on the other.
        """
        return Comparison(
            only_here=tuple(one for one in self.only_here if one.id in kept),
            only_there=tuple(one for one in self.only_there if one.id in kept),
            parted=tuple(one for one in self.parted if one.id in kept),
            changed=tuple(one for one in self.changed if one.id in kept),
            alike=tuple(one for one in self.alike if one in kept),
        )

    @property
    def differs(self) -> bool:
        """Whether there is anything to list at all."""
        return bool(self.only_here or self.only_there or self.parted or self.changed)


def _by_id(
    side: tuple[tuple[Ticket, ...], tuple[Ticket, ...]],
) -> dict[str, tuple[Ticket, bool]]:
    """One side's tickets by id, each marked closed or not, live first and in knot's order.

    knot lists a ticket either as live or as closed, never both; were a hand-edited backlog to
    do so, the live copy is the one kept, since that is the one the side is still working.
    """
    live, closed = side
    held: dict[str, tuple[Ticket, bool]] = {}
    for one, shut in chain(((one, False) for one in live), ((one, True) for one in closed)):
        held.setdefault(one.id, (one, shut))
    return held


def _changes(here: Ticket, there: Ticket) -> tuple[Change, ...]:
    """Every compared field that reads differently in the two copies."""
    return tuple(
        Change(field=name, here=str(getattr(here, name)), there=str(getattr(there, name)))
        for name in FIELDS
        if getattr(here, name) != getattr(there, name)
    )
