"""What a reader asked to see, read from a query string and checked against the project."""

from dataclasses import dataclass

from knotview.values.project import Project
from knotview.values.ticket import Ticket

# How a list may be ordered. Priority first is the backlog's own order: knot numbers zero highest,
# so ascending priority is descending urgency, which is why this is not simply a sort direction.
ORDERS = ("priority", "leverage", "level", "updated", "created", "title", "id")

# What a filter may be set to and mean "everything". Declared rather than an empty string, so a
# reader can see in the URL that a filter is deliberately unset.
ANY = "any"

# What the assignee filter is set to and mean "nobody". An assignee is a name, and no name is
# spelled as an empty string in a query, so nobody needs a word of its own to be a link.
NOBODY = "nobody"


@dataclass(frozen=True, kw_only=True)
class Selection:  # pylint: disable=too-many-instance-attributes
    """One reader's filters, as a value rather than a handful of arguments.

    A value because every page shares them and because the panel has to hand them back: a filtered
    list whose links forget the filter is a list nobody can navigate. Holding them together also
    makes the one rule about them obvious, which is that a filter naming something the project does
    not declare is dropped rather than obeyed. A status that no longer exists would otherwise
    silently select nothing, and an empty page reads as a quiet backlog rather than as a stale
    link.

    It holds more attributes than the linter's default allows because the fields are the query
    string this panel defines, one per filter the URL carries, and query_string and matches
    read them in one place; a split would move the filter list away from the code that keeps
    every link honest.
    """

    type: str = ANY
    status: str = ANY
    priority: str = ANY
    mode: str = ANY
    assignee: str = ANY
    tag: str = ANY
    component: str = ANY
    query: str = ""
    order: str = "priority"
    closed: bool = False

    @classmethod
    def asked(cls, project: Project, given: dict[str, str]) -> "Selection":
        """The selection a query string asked for.

        Anything the project does not declare is dropped rather than obeyed.
        """
        return cls(
            type=_known(given.get("type"), project.types),
            status=_known(given.get("status"), project.statuses),
            priority=_known(given.get("priority"), tuple(str(one) for one in project.priorities)),
            mode=_known(given.get("mode"), project.modes),
            assignee=(given.get("assignee") or ANY).strip() or ANY,
            tag=(given.get("tag") or ANY).strip() or ANY,
            component=(given.get("component") or ANY).strip() or ANY,
            query=(given.get("q") or "").strip(),
            order=_known(given.get("order"), ORDERS, fallback="priority"),
            closed=(given.get("closed") or "").lower() in ("1", "true", "yes", "on"),
        )

    @property
    def filtering(self) -> bool:
        """Whether anything is actually narrowed, which is what decides showing a clear link."""
        return bool(self.applied())

    def applied(self) -> tuple[tuple[str, str], ...]:
        """Every filter that is set, as the reader would name it, for the summary line."""
        named = (
            ("type", self.type),
            ("status", self.status),
            ("priority", self.priority),
            ("mode", self.mode),
            ("assignee", self.assignee),
            ("tag", self.tag),
            ("component", self.component),
            ("matching", self.query),
        )
        return tuple((field, value) for field, value in named if value and value != ANY)

    def query_string(self, **changes: str) -> str:
        """This selection as a query string, with whatever a link is changing about it.

        Built here rather than in a template so that a link cannot lose a filter by forgetting a
        field: adding a filter means adding it to this one place, and every link carries it.
        """
        held = {
            "type": self.type,
            "status": self.status,
            "priority": self.priority,
            "mode": self.mode,
            "assignee": self.assignee,
            "tag": self.tag,
            "component": self.component,
            "q": self.query,
            "order": self.order,
            "closed": "1" if self.closed else "",
        }
        held.update(changes)
        kept = [
            f"{field}={value}"
            for field, value in held.items()
            if value and value != ANY and not (field == "order" and value == "priority")
        ]
        return "&".join(kept)

    def matches(self, ticket: Ticket) -> bool:
        """Whether that ticket is one of the ones asked for."""
        return all(
            (
                self.type in (ANY, ticket.type),
                self.status in (ANY, ticket.status),
                self.priority in (ANY, str(ticket.priority)),
                self.mode in (ANY, ticket.mode),
                self._assigned(ticket),
                self.tag == ANY or self.tag in ticket.tags,
                self.component in (ANY, str(ticket.component)),
                self._mentions(ticket),
            )
        )

    def ordered(self, tickets: tuple[Ticket, ...]) -> tuple[Ticket, ...]:
        """Those tickets in the order asked for, with a stable tie-break on the id.

        Stable because a list that reshuffles between two reads of the same backlog is a list nobody
        can scan twice, and two tickets of one priority updated in the same second are ordinary.
        """
        keys = {
            "priority": lambda held: (held.priority, held.id),
            # Highest leverage first and lowest level first, with the rows knot gave no number
            # (a closed row, a cycle) after every row it did.
            "leverage": lambda held: (held.leverage is None, -(held.leverage or 0), held.id),
            "level": lambda held: (held.level is None, held.level or 0, held.id),
            "updated": lambda held: (held.updated or "", held.id),
            "created": lambda held: (held.created or "", held.id),
            "title": lambda held: (held.title.lower(), held.id),
            "id": lambda held: (held.id,),
        }
        descending = self.order in ("updated", "created")
        return tuple(sorted(tickets, key=keys[self.order], reverse=descending))

    def _assigned(self, ticket: Ticket) -> bool:
        """Whether the ticket is assigned the way the filter asks: to anyone, nobody, or a name."""
        if self.assignee == ANY:
            return True
        if self.assignee == NOBODY:
            return not ticket.assignee
        return ticket.assignee == self.assignee

    def _mentions(self, ticket: Ticket) -> bool:
        """Whether the text asked for appears anywhere a reader would look for it.

        The id, the title and the tags, which is what somebody typing into a search box means. Not
        the body: a panel that matched a word buried in a design section would answer with tickets
        whose titles have nothing to do with the question, and the reader cannot see why they are
        there.
        """
        if not self.query:
            return True
        looking = self.query.lower()
        return (
            looking in ticket.id.lower()
            or looking in ticket.title.lower()
            or any(looking in tag.lower() for tag in ticket.tags)
        )


def _known(given: str | None, allowed: tuple[str, ...], *, fallback: str = ANY) -> str:
    """That value if the project declares it, and otherwise everything.

    Dropping an unknown value rather than refusing it is deliberate. A panel is navigated by hand
    and by link, and a stale bookmark naming a status somebody renamed should show the backlog
    rather than an error page.
    """
    if given is None:
        return fallback
    stated = given.strip()
    return stated if stated in allowed else fallback
