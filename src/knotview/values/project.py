"""What a knot project says about itself, which is what makes this panel dynamic."""

from collections.abc import Iterable
from dataclasses import dataclass

from knotview.values.document import Document
from knotview.values.ticket import Ticket


@dataclass(frozen=True, kw_only=True)
class Project:  # pylint: disable=too-many-instance-attributes
    """The configuration the panel is shaped by, read from the project rather than assumed.

    Every list here is the project's own. A panel with its own idea of which types exist is a panel
    that is wrong about the next repository it is pointed at: knot lets a project declare its types,
    its statuses, which status is active and which are terminal, its modes and its priority range,
    and all of that drives the navigation rather than decorating it.

    The active and terminal statuses matter more than they look. They are what lets the panel say
    "in progress" and "closed" without knowing those words: one project's active status may be
    `doing` and another's `in_progress`, and a panel that hardcoded either would mislabel the other.

    Documents are ordered and counted here too, because both depend on the project's own
    declarations: which types it allows, in what order, and which it requires before a status. knot
    itself gives a ticket's documents in id order from one command and alphabetically from another,
    so a page that took either would disagree with the next page. These helpers take a Ticket, which
    reverses the usual direction of this layer (Ticket.open_blockers takes bare statuses); they need
    the project's configuration and the ticket's documents together, and tickets never import this.

    It holds more attributes than the linter's default allows because the fields are what knot
    info reports; grouping them into nested values would hide the configuration this panel
    mirrors.
    """

    name: str
    prefix: str
    knot_version: str
    types: tuple[str, ...]
    statuses: tuple[str, ...]
    active_status: str
    terminal_statuses: tuple[str, ...]
    modes: tuple[str, ...]
    priority_range: tuple[int, int]
    tickets_path: str
    live_count: int
    archive_count: int
    doc_types: tuple[str, ...] = ()
    # What a ticket must own before it may enter a status: the project's declared statuses first in
    # their declared order, then any others in the order knot gave them, so none is dropped.
    required_docs: tuple[tuple[str, tuple[str, ...]], ...] = ()
    doc_count: int = 0
    # Where knot keeps documents and the project itself, absolute as knot states them. The docs
    # directory sits inside the tickets directory unless `.knot.edn` moves it.
    docs_path: str = ""
    project_root: str = ""

    @property
    def open_statuses(self) -> tuple[str, ...]:
        """Every status that is not terminal, in the order the project declared them."""
        return tuple(status for status in self.statuses if status not in self.terminal_statuses)

    def ordered(self, documents: Iterable[Document]) -> tuple[Document, ...]:
        """Documents in the project's declared type order, then by title, undeclared types last."""
        return tuple(
            sorted(
                documents,
                key=lambda one: (self._rank(one.type), one.title.casefold(), one.id),
            )
        )

    def ordered_types(self, types: Iterable[str]) -> tuple[str, ...]:
        """Type names in the same order, for a listing row that states only the names."""
        return tuple(sorted(types, key=lambda kind: (self._rank(kind), kind)))

    def types_of(self, ticket: Ticket) -> tuple[str, ...]:
        """The types a ticket owns, in order, from whichever of knot's two answers it carries.

        A document whose file names no type owns none, rather than an empty type a page would draw
        as a blank tag.
        """
        owned = {one.type for one in ticket.documents} or set(ticket.doc_types)
        return self.ordered_types(kind for kind in owned if kind)

    def missing_documents(self, ticket: Ticket) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Each status whose required documents the ticket does not own, with the types it lacks.

        Every such status, the ticket's own included: knot checks the rule only when a ticket moves,
        so a ticket that entered a status before the rule existed sits there without them and knot
        says nothing. Which of these a page shows is the page's decision.
        """
        owned = set(self.types_of(ticket))
        gaps = (
            (status, tuple(kind for kind in required if kind not in owned))
            for status, required in self.required_docs
        )
        return tuple((status, lacking) for status, lacking in gaps if lacking)

    def is_live(self, ticket: Ticket) -> bool:
        """Whether the ticket is in a status the project has not declared terminal.

        The one test of whether required documents still matter: knot checks them only when a
        ticket moves, and a closed ticket makes no more moves.
        """
        return ticket.status not in self.terminal_statuses

    def missing_by_type(self, ticket: Ticket) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Each type the ticket lacks, in declared order, with every status that needs it.

        The same facts as `missing_documents`, turned round: a reader asks what document is
        missing before asking which status wants it, and one type needed by two statuses is one
        thing to attach, not two.
        """
        needing: dict[str, list[str]] = {}
        for status, lacking in self.missing_documents(ticket):
            for kind in lacking:
                needing.setdefault(kind, []).append(status)
        return tuple((kind, tuple(needing[kind])) for kind in self.ordered_types(needing))

    def _rank(self, kind: str) -> int:
        """Where a type falls in the declared order, with an undeclared type after all of them."""
        return self.doc_types.index(kind) if kind in self.doc_types else len(self.doc_types)

    @property
    def priorities(self) -> tuple[int, ...]:
        """Every priority the project permits, lowest number first, which is highest first."""
        lowest, highest = self.priority_range
        return tuple(range(lowest, highest + 1))
