"""What a reader asked to see, read from a query string and checked against the project."""

import re
from collections.abc import Iterable
from dataclasses import dataclass, replace
from urllib.parse import quote

from knotview.values.project import Project
from knotview.values.ticket import Ticket

# Where one sentence ends and the next begins, for the excerpt a deep search shows.
_SENTENCES = re.compile(r"(?<=[.!?])\s+|\n{2,}")

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
    deep: bool = False
    order: str = "priority"
    closed: bool = False
    # The document filters: the types a ticket must own, in the project's declared order; tickets
    # owning none; and live tickets missing a type their project requires. Three fields because
    # the two options cannot share the types' parameter: a project may declare a type named none.
    docs: tuple[str, ...] = ()
    undocumented: bool = False
    lacking: bool = False

    @classmethod
    def asked(
        cls, project: Project, given: dict[str, str], docs: Iterable[str] = ()
    ) -> "Selection":
        """The selection a query string asked for.

        Anything the project does not declare is dropped rather than obeyed. The document types
        come separately, as the repeated values a single-valued mapping cannot hold. Asking for
        tickets that own nothing clears the types, since no ticket could satisfy both. Lacking a
        required type means nothing where the project requires none, so it is dropped there like
        an undeclared type rather than emptying the list for a reason no chip could explain.
        """
        undocumented = _ticked(given.get("nodocs"))
        return cls(
            type=_known(given.get("type"), project.types),
            status=_known(given.get("status"), project.statuses),
            priority=_known(given.get("priority"), tuple(str(one) for one in project.priorities)),
            mode=_known(given.get("mode"), project.modes),
            assignee=(given.get("assignee") or ANY).strip() or ANY,
            tag=(given.get("tag") or ANY).strip() or ANY,
            component=(given.get("component") or ANY).strip() or ANY,
            query=(given.get("q") or "").strip(),
            deep=_ticked(given.get("deep")),
            order=_known(given.get("order"), ORDERS, fallback="priority"),
            closed=_ticked(given.get("closed")),
            docs=() if undocumented else project.ordered_types(set(docs) & set(project.doc_types)),
            undocumented=undocumented,
            lacking=_ticked(given.get("lacking")) and bool(project.required_docs),
        )

    @property
    def filtering(self) -> bool:
        """Whether anything is actually narrowed, which is what decides showing a clear link."""
        return bool(self.applied())

    def applied(self) -> tuple[tuple[str, str], ...]:
        """Every filter that is set, as the reader would name it, for the summary line."""
        return tuple((label, value) for label, value, _ in self.chips())

    def chips(self) -> tuple[tuple[str, str, str], ...]:
        """Every applied filter as (label, value, the query string without it).

        Each chip carries its own way out, so removing one of several ticked document types keeps
        the others: a filter the reader named once is dropped once.
        """
        return tuple((label, value, self._dropping(label)) for label, value in self._set())

    def without(self, label: str) -> str:
        """This selection as a query string with that one filter dropped, for a chip's link."""
        return self._dropping(label)

    def having(self, kind: str) -> str:
        """The query string with its document types replaced by that one, every other filter kept.

        Built from a copy rather than through `query_string(doc=...)`, whose keyword changes hold
        one value each and would add the type to those already chosen: a link that promises the
        tickets owning a spec must not also require the plan the reader had ticked. Owning nothing
        is cleared too, since it would empty the types again.
        """
        return replace(self, docs=(kind,), undocumented=False).query_string()

    def _dropping(self, label: str) -> str:
        """The query string with the filter named by that label removed and every other kept."""
        if label.startswith("has "):
            left = tuple(one for one in self.docs if one != label.removeprefix("has "))
            return replace(self, docs=left).query_string()
        dropped = {"none attached": "nodocs", "missing a required type": "lacking"}
        parameter = dropped.get(label) or next(
            (param for shown, param, _ in self._named() if shown == label), label
        )
        return self.query_string(**{parameter: ""})

    def _set(self) -> tuple[tuple[str, str], ...]:
        """Each applied filter as (label the reader sees, value), documents last."""
        plain = tuple((label, value) for label, _, value in self._named())
        documents = tuple((f"has {one}", "") for one in self.docs)
        options = (("none attached", ""),) * self.undocumented + (
            ("missing a required type", ""),
        ) * self.lacking
        return plain + documents + options

    def _named(self) -> tuple[tuple[str, str, str], ...]:
        """Each applied single-valued filter as (label, query parameter, value)."""
        named = (
            ("type", "type", self.type),
            ("status", "status", self.status),
            ("priority", "priority", self.priority),
            ("mode", "mode", self.mode),
            ("assignee", "assignee", self.assignee),
            ("tag", "tag", self.tag),
            ("component", "component", self.component),
            ("matching", "q", self.query),
        )
        return tuple(one for one in named if one[2] and one[2] != ANY)

    def query_string(self, **changes: str) -> str:
        """This selection as a query string, with whatever a link is changing about it.

        Built here rather than in a template so that a link cannot lose a filter by forgetting a
        field: adding a filter means adding it to this one place, and every link carries it.

        A change names one value per field, so it refuses the document types, which repeat: merged
        here, a named type would be added to those already chosen rather than replace them. A link
        to one type goes through `having`.
        """
        if "doc" in changes:
            raise TypeError("query_string changes one value per field; use having() for a type")
        held = {
            "type": self.type,
            "status": self.status,
            "priority": self.priority,
            "mode": self.mode,
            "assignee": self.assignee,
            "tag": self.tag,
            "component": self.component,
            "q": self.query,
            "deep": "1" if self.deep else "",
            "order": self.order,
            "closed": "1" if self.closed else "",
            "nodocs": "1" if self.undocumented else "",
            "lacking": "1" if self.lacking else "",
        }
        held.update(changes)
        pairs = [
            (field, value) for field, value in held.items() if field not in ("nodocs", "lacking")
        ]
        pairs += [("doc", one) for one in self.docs]
        pairs += [(field, held[field]) for field in ("nodocs", "lacking")]
        kept = [
            f"{field}={quote(value, safe='')}"
            for field, value in pairs
            if value and value != ANY and not (field == "order" and value == "priority")
        ]
        return "&".join(kept)

    def matches(self, ticket: Ticket, project: Project) -> bool:
        """Whether that ticket is one of the ones asked for, by the project's own declarations."""
        return self._documented(ticket, project) and all(
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

    def _documented(self, ticket: Ticket, project: Project) -> bool:
        """Whether the ticket's documents are the ones asked for.

        Owning means owning every ticked type. Lacking counts only a live ticket: a closed one is
        past the moves its project gates, so what it would have needed means nothing now.
        """
        owned = set(project.types_of(ticket))
        live = project.is_live(ticket)
        return (
            set(self.docs) <= owned
            and (not self.undocumented or not owned)
            and (not self.lacking or (live and bool(project.missing_documents(ticket))))
        )

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
        the body unless the reader asked for that too: a panel that matched a word buried in a
        design section would answer with tickets whose titles have nothing to do with the question,
        which is why a deep search shows the sentence that matched under each title.
        """
        if not self.query:
            return True
        looking = self.query.lower()
        return (
            looking in ticket.id.lower()
            or looking in ticket.title.lower()
            or any(looking in tag.lower() for tag in ticket.tags)
            or (self.deep and self.excerpt(ticket) is not None)
        )

    def excerpt(self, ticket: Ticket) -> str | None:
        """The first sentence of the ticket's text that holds the query, or nothing."""
        if not self.query:
            return None
        looking = self.query.lower()
        for text in ticket.sections.values():
            for sentence in _SENTENCES.split(text):
                if looking in sentence.lower():
                    return " ".join(sentence.split())
        return None


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


def _ticked(held: str | None) -> bool:
    """Whether a checkbox-style parameter is on, as a browser or a hand-written link spells it."""
    return (held or "").lower() in ("1", "true", "yes", "on")
