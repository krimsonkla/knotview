"""A backlog declared in a test, so every page can be asserted without a process."""

from dataclasses import dataclass, field

from knotview.values.criterion import Criterion
from knotview.values.missing_ticket import MissingTicket
from knotview.values.project import Project
from knotview.values.reference import Reference
from knotview.values.ticket import Ticket
from knotview.values.unreadable_backlog import UnreadableBacklog

PROJECT = Project(
    name="probe",
    prefix="pro",
    knot_version="0.12.0",
    types=("bug", "feature", "task", "epic", "chore"),
    statuses=("open", "in_progress", "closed"),
    active_status="in_progress",
    terminal_statuses=("closed",),
    modes=("afk", "hitl"),
    priority_range=(0, 4),
    tickets_path="/nowhere/.tickets",
    live_count=3,
    archive_count=1,
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
    children=(Reference(id="pro-01m2bbbbbbbb", title="The child", status="in_progress"),),
    sections={"": "Text before any heading.", "description": "What for.", "notes": "A note."},
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
    integrity_value: tuple[str, ...] = ()
    digests: list[str] = field(default_factory=lambda: ["d1"])
    digest_calls: int = 0

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

    def integrity(self) -> tuple[str, ...]:
        """The declared integrity lines."""
        return self.integrity_value

    def digest(self) -> str:
        """The next declared digest, refusing once the sequence is spent."""
        self.digest_calls += 1
        if not self.digests:
            raise UnreadableBacklog("the tickets directory went away", advice="point it back")
        return self.digests.pop(0)


class RefusingBacklog:  # pylint: disable=too-few-public-methods
    """A backlog that cannot be read at all, which is the wrong-directory case.

    Every port method is the same refusal, bound as attributes rather than written eight times.
    """

    def _refuse(self, *_: object) -> None:
        raise UnreadableBacklog("no knot project here", advice="run knot init, or point elsewhere")

    project = live = closed = ready = blocked = ticket = integrity = digest = _refuse
