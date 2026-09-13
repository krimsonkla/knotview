"""One ticket, as this panel holds it."""

from dataclasses import dataclass, field

from knotview.values.criterion import Criterion
from knotview.values.reference import Reference


@dataclass(frozen=True, kw_only=True)
class Ticket:  # pylint: disable=too-many-instance-attributes
    """A ticket and everything the panel shows about it.

    Assembled from whichever knot command answered, which is why so much is optional. A listing
    gives the summary; `show` adds the sections, the notes and both directions of the
    graph. The same value carries both so a template does not have to know which command the reader
    used, and a field nobody was told about is absent rather than invented.

    The sections are kept as the project wrote them rather than as a single rendered body. A knot
    ticket is a small document with headings its author chose, and flattening it would lose the
    distinction between what a ticket is for and how it was designed, which is most of what a reader
    came for.

    It holds more attributes than the linter's default allows because the fields are knot's
    record shape; grouping them into nested values would hide the schema this reader mirrors.
    """

    id: str
    title: str
    status: str
    type: str
    priority: int
    mode: str | None = None
    assignee: str | None = None
    parent: str | None = None
    created: str | None = None
    updated: str | None = None
    closed: str | None = None
    tags: tuple[str, ...] = ()
    external_refs: tuple[str, ...] = ()
    acceptance: tuple[Criterion, ...] = ()
    blockers: tuple[Reference, ...] = ()
    blocking: tuple[Reference, ...] = ()
    children: tuple[Reference, ...] = ()
    linked: tuple[Reference, ...] = ()
    sections: dict[str, str] = field(default_factory=dict)

    @property
    def met(self) -> int:
        """How many acceptance criteria are ticked."""
        return sum(1 for criterion in self.acceptance if criterion.done)

    @property
    def criteria(self) -> int:
        """How many acceptance criteria there are, which is zero on a ticket that states none."""
        return len(self.acceptance)

    @property
    def unmet(self) -> tuple[Criterion, ...]:
        """The criteria still open, which is what a reader asking "what is left" wants."""
        return tuple(criterion for criterion in self.acceptance if not criterion.done)

    @property
    def open_blockers(self) -> tuple[Reference, ...]:
        """The blockers that are not closed, which are the ones actually blocking."""
        return tuple(blocker for blocker in self.blockers if blocker.status != "closed")

    @property
    def notes(self) -> str | None:
        """The notes section, which knot appends to rather than rewrites.

        Named rather than read out of the section map by a template, because it is the one section
        with a meaning the panel relies on: it is a timeline, and it is where the reasoning behind a
        decision ends up.
        """
        return self.sections.get("notes")

    def narrative(self) -> tuple[tuple[str, str], ...]:
        """Every section except the notes, in the order the ticket holds them.

        The notes are separated because they read as a log while the rest reads as a document, and a
        page that interleaved them would bury the description under three screens of history.
        """
        return tuple(
            (heading, text) for heading, text in self.sections.items() if heading != "notes"
        )
