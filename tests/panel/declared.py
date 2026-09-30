"""A backlog declared in a test, so every page can be asserted without a process."""

from dataclasses import dataclass, field, replace

from knotview.values.attention import Attention
from knotview.values.criterion import Criterion
from knotview.values.dependency import Dependency
from knotview.values.document import Document
from knotview.values.missing_document import MissingDocument
from knotview.values.missing_ticket import MissingTicket
from knotview.values.project import Project
from knotview.values.reference import Reference
from knotview.values.ticket import Ticket
from knotview.values.unreadable_backlog import UnreadableBacklog
from knotview.values.issue import Issue

PROJECT = Project(
    name="probe",
    prefix="pro",
    knot_version="0.15.0",
    types=("bug", "feature", "task", "epic", "chore"),
    statuses=("open", "in_progress", "closed"),
    active_status="in_progress",
    terminal_statuses=("closed",),
    modes=("afk", "hitl"),
    priority_range=(0, 4),
    tickets_path="/nowhere/.tickets",
    live_count=3,
    archive_count=1,
    doc_types=("spec", "plan", "other"),
    doc_count=2,
)


def ticket(identifier: str, **held: object) -> Ticket:
    """A ticket with sensible defaults, so a test names only what it is about."""
    given: dict = {
        "id": identifier,
        "title": f"Ticket {identifier}",
        "status": "open",
        "type": "task",
        "priority": 2,
        "created": "2026-09-01T10:00:00.000000Z",
        "updated": "2026-09-02T10:00:00.000000Z",
    }
    given.update(held)
    return Ticket(**given)


PARENT = ticket(
    "pro-01m2aaaaaaaa",
    title="The parent",
    type="epic",
    priority=1,
    tags=("p0", "auth"),
    acceptance=(
        Criterion(title="first thing", done=True),
        Criterion(title="second thing", done=False),
    ),
    children=(
        Reference(id="pro-01m2bbbbbbbb", title="The child", status="in_progress"),
        Reference(id="pro-01m2cccccccc", title="The closed one", status="closed"),
    ),
    sections={"": "Text before any heading.", "description": "What for.", "notes": "A note."},
    # As `show` states them: id, title and type, owned by the parent, nothing else read.
    documents=(
        Document(
            id="pro-01m2aaaaaaaa-d2plan",
            ticket="pro-01m2aaaaaaaa",
            title="Rollout plan",
            type="plan",
        ),
        Document(
            id="pro-01m2aaaaaaaa-d7spec",
            ticket="pro-01m2aaaaaaaa",
            title="Design spec",
            type="spec",
        ),
    ),
)

# The parent's documents as `document list` and `document show` state them, derived from what
# `show` states so the two cannot disagree: the same documents, with their times and bodies.
PARENT_DOCUMENTS = tuple(
    replace(
        one,
        created="2026-09-02T10:00:00.000000Z",
        updated="2026-09-06T10:00:00.000000Z",
        body=f"The {one.type}.\n",
    )
    for one in PARENT.documents
)
CHILD = ticket(
    "pro-01m2bbbbbbbb",
    title="The child",
    status="in_progress",
    mode="afk",
    parent="pro-01m2aaaaaaaa",
    updated="2026-09-04T10:00:00.000000Z",
    blockers=(
        Reference(id="pro-01m2cccccccc", title="The closed one", status="closed"),
        Reference(id="pro-01m2zzzzzzzz", title="", status="", missing=True),
    ),
    linked=(Reference(id="pro-01m2dddddddd", title="The orphan", status="open"),),
    external_refs=("https://example.test/1",),
)
ORPHAN = ticket("pro-01m2dddddddd", title="The orphan", type="bug", priority=3, assignee="someone")
CLOSED = ticket(
    "pro-01m2cccccccc",
    title="The closed one",
    status="closed",
    type="chore",
    priority=4,
    parent="pro-01m2aaaaaaaa",
    closed="2026-08-02T10:00:00.000000Z",
)


CHILD_DEPENDENCIES = Dependency(
    id="pro-01m2bbbbbbbb",
    title="The child",
    status="in_progress",
    deps=(
        Dependency(id="pro-01m2cccccccc", title="The closed one", status="closed"),
        Dependency(id="pro-01m2zzzzzzzz", title="", status="", missing=True),
    ),
)


@dataclass(kw_only=True)
class DeclaredBacklog:  # pylint: disable=too-many-instance-attributes
    """A Backlog over tuples, counting how often the digest is asked for.

    One attribute per answer the port gives, plus the digest sequence and its call count, which
    is why it holds more than the usual seven.
    """

    project_value: Project = PROJECT
    live_value: tuple[Ticket, ...] = (PARENT, CHILD, ORPHAN)
    closed_value: tuple[Ticket, ...] = (CLOSED,)
    ready_value: tuple[Ticket, ...] = (PARENT, ORPHAN)
    blocked_value: tuple[Ticket, ...] = (CHILD,)
    attention_value: Attention = field(
        default_factory=lambda: Attention(in_progress=(CHILD,), ready_to_close=(), stale=())
    )
    integrity_value: tuple[Issue, ...] = ()
    documents_value: dict[str, tuple[Document, ...]] = field(
        default_factory=lambda: {PARENT.id: PARENT_DOCUMENTS}
    )
    digests: list[str] = field(default_factory=lambda: ["d1"])
    digest_calls: int = 0
    # Makes the document list refuse for a ticket that exists, as knot refusing it for any other
    # reason would, to drive the ticket page's fallback to the documents `show` stated.
    documents_refused: bool = False

    def project(self) -> Project:
        """The declared project."""
        return self.project_value

    def live(self) -> tuple[Ticket, ...]:
        """The declared live tickets."""
        return self.live_value

    def closed(self) -> tuple[Ticket, ...]:
        """The declared closed tickets."""
        return self.closed_value

    def ready(self) -> tuple[Ticket, ...]:
        """The declared ready queue."""
        return self.ready_value

    def blocked(self) -> tuple[Ticket, ...]:
        """The declared blocked queue."""
        return self.blocked_value

    def ticket(self, identifier: str) -> Ticket:
        """One declared ticket by id, refusing an unknown one the way knot's not_found does."""
        for held in (*self.live_value, *self.closed_value):
            if held.id == identifier:
                return held
        raise MissingTicket(
            identifier, message=f"knot show was refused: no ticket matching {identifier}"
        )

    def documents(self, ticket_id: str) -> tuple[Document, ...]:
        """A declared ticket's documents with their times, refusing an unknown ticket as knot
        does."""
        self.ticket(ticket_id)
        if self.documents_refused:
            raise UnreadableBacklog("refused", advice="", code="invalid_argument")
        return tuple(replace(one, body=None) for one in self.documents_value.get(ticket_id, ()))

    def document(self, document_id: str) -> Document:
        """One declared document with its body, resolved as knot resolves an id.

        The whole id first; then, as knot does, a start that names the owning ticket in full and
        goes on into the document's part, matched against that ticket's documents only. A start
        several share is refused, as is one shorter than a ticket's id. Resolving here rather than
        in the page keeps knot's id scheme out of the panel, which only compares the id knot
        answered with.
        """
        held = [one for owned in self.documents_value.values() for one in owned]
        exact = [one for one in held if one.id == document_id]
        begun = [
            one
            for one in held
            if document_id.startswith(f"{one.ticket}-d") and one.id.startswith(document_id)
        ]
        if exact or len(begun) == 1:
            return (exact or begun)[0]
        raise MissingDocument(document_id, message=f"document not found: {document_id}")

    def attention(self) -> Attention:
        """The declared primer report."""
        return self.attention_value

    def dependencies(self, identifier: str) -> Dependency:
        """The child's declared tree, and a leaf for anything else."""
        if identifier == CHILD_DEPENDENCIES.id:
            return CHILD_DEPENDENCIES
        return Dependency(id=identifier, title="", status="open")

    def integrity(self) -> tuple[Issue, ...]:
        """The declared integrity issues."""
        return self.integrity_value

    def digest(self) -> str:
        """The next declared digest, refusing once the sequence is spent."""
        self.digest_calls += 1
        if not self.digests:
            raise UnreadableBacklog("the tickets directory went away", advice="point it back")
        return self.digests.pop(0)


class RefusingBacklog:  # pylint: disable=too-few-public-methods
    """A backlog that cannot be read at all, which is the wrong-directory case.

    Every port method is the same refusal, bound as attributes rather than written ten times.
    """

    def _refuse(self, *_: object) -> None:
        raise UnreadableBacklog("no knot project here", advice="run knot init, or point elsewhere")

    project = live = closed = ready = blocked = ticket = _refuse
    dependencies = attention = integrity = digest = documents = document = _refuse
