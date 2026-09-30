"""The panel: every route a GET, every answer a page, a redirect, or a digest."""

import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import quote

from fastapi import FastAPI, Request
from fastapi.responses import (
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

from knotview.panel.overview import Overview
from knotview.panel.prose import outlined
from knotview.panel.prose import rendered as prose
from knotview.panel.selection import ANY, ORDERS, Selection
from knotview.panel.tags import COOKIE, Tags
from knotview.panel.tree import Tree
from knotview.reading.backlog import Backlog
from knotview.reading.snapshot import Snapshot
from knotview.values.document import Document
from knotview.values.missing_document import MissingDocument
from knotview.values.missing_ticket import MissingTicket
from knotview.values.ticket import Ticket
from knotview.values.unreadable_backlog import UnreadableBacklog

HERE = Path(__file__).resolve().parent

# The names a browser may address the panel by. It binds loopback, but a page on any other site
# can still make a browser send requests to a loopback port under that site's own host name, and
# the backlog would answer; refusing every host but these closes that door.
HOSTS = ("127.0.0.1", "localhost", "[::1]")


class Pages:
    """Every page the panel serves, over one backlog.

    A class rather than a set of closures so that which backlog a page reads is a named
    attribute, and so that assembling the app (mounting the static files, registering the
    exception handler, writing out the route table) is separate from rendering a page.

    Read-only, and structurally so: every route in ROUTES is a GET, there is no form, and the
    backlog port has no method that writes. The backlog stays driven by whatever writes it, and
    this watches.

    Each page, and each page for a refusal, is a plain function rather than a coroutine. Its reads
    start knot and wait for it, and FastAPI and Starlette run a plain handler in their thread pool,
    so one page's reads do not hold every other request behind them. That also means the backlog
    is read from several threads at once.
    """

    def __init__(self, backlog: Backlog, *, templates: Jinja2Templates) -> None:
        self.backlog = backlog
        self.templates = templates

    def _rendered(
        self, request: Request, template: str, *, status: int = 200, **context: object
    ) -> HTMLResponse:
        """One page, with what every page needs already in it: the project and the reader's tags."""
        project = self.backlog.project()
        known = sorted({tag for one in self.backlog.live() for tag in one.tags})
        return self.templates.TemplateResponse(
            request=request,
            name=template,
            context={
                "project": project,
                "orders": ORDERS,
                "any": ANY,
                "tags": _tags(request),
                "known_tags": known,
                "here": request.url.path + (f"?{request.url.query}" if request.url.query else ""),
                **context,
            },
            status_code=status,
        )

    def _narrowed(self, request: Request, tickets: tuple[Ticket, ...]) -> tuple[Ticket, ...]:
        """Those tickets seen through the reader's chosen tags."""
        return _tags(request).narrow(tickets)

    def tags(self, request: Request, add: str = "", drop: str = "", clear: str = "") -> Response:
        """Change the reader's chosen tags and go back to the page they were on.

        A GET like every other route, since it changes nothing about the backlog: the choice is
        kept in a cookie in the reader's browser. The way back must be a path on this panel, so
        a link from elsewhere cannot use it to send a reader somewhere else.
        """
        chosen = _tags(request)
        if clear:
            chosen = Tags()
        if drop:
            chosen = chosen.dropping(drop)
        if add:
            chosen = chosen.adding(add)
        back = request.query_params.get("back") or "/"
        if not back.startswith("/") or back.startswith("//"):
            back = "/"
        answer = RedirectResponse(back, status_code=303)
        if chosen.chosen:
            answer.set_cookie(COOKIE, chosen.cookie(), samesite="strict", httponly=True)
        else:
            answer.delete_cookie(COOKIE)
        return answer

    def missing(self, request: Request, refusal: MissingTicket) -> HTMLResponse:
        """The page for a ticket that is not there: a 404 offering the list, not a 503."""
        return self._rendered(
            request,
            "unknown.html",
            status=404,
            looking_for=f"ticket called {refusal.identifier}",
            selection=Selection(),
        )

    def missing_document(self, request: Request, refusal: MissingDocument) -> HTMLResponse:
        """The page for a document that is not there: a 404 offering the list, like a ticket's."""
        return self._rendered(
            request,
            "unknown.html",
            status=404,
            looking_for=f"document called {refusal.identifier}",
            selection=Selection(),
        )

    def unreadable(self, request: Request, refusal: UnreadableBacklog) -> HTMLResponse:
        """Say what could not be read and what to do about it, rather than a stack trace.

        A panel pointed at the wrong directory is the ordinary first mistake, and the page that
        admits it is worth more than the one that works once everything is right.
        """
        return self.templates.TemplateResponse(
            request=request,
            name="unreadable.html",
            context={"refusal": refusal},
            status_code=503,
        )

    def overview(self, request: Request) -> HTMLResponse:
        """The backlog counted by type, by status and by priority, with the queues beside it.

        Every count equals the list its link opens. Both are narrowed by the reader's tags and by
        nothing else: the overview ignores its own query string, as every other page does, so a
        filter left in its URL cannot ride into a card's link while the count ignores it. The one
        assumption is a clean check: a ticket in a terminal status that knot has not archived is
        listed under its status but not counted among the closed, and the integrity card says so.
        """
        seen = Snapshot.read(self.backlog)
        chosen = _tags(request)
        if chosen.chosen:
            live = chosen.narrow(seen.live)
            # The primer's rows carry no tags, so they are narrowed by id against the live tickets
            # that passed, not by tags of their own; otherwise every attention card would empty
            # the moment a tag was chosen.
            kept = {one.id for one in live}
            seen = replace(
                seen,
                live=live,
                closed=chosen.narrow(seen.closed),
                ready=chosen.narrow(seen.ready),
                blocked=chosen.narrow(seen.blocked),
                attention=replace(
                    seen.attention,
                    in_progress=_among(seen.attention.in_progress, kept),
                    ready_to_close=_among(seen.attention.ready_to_close, kept),
                    stale=_among(seen.attention.stale, kept),
                ),
            )
        return self._rendered(
            request,
            "overview.html",
            overview=Overview.over(seen),
            selection=Selection(),
        )

    def tickets(self, request: Request) -> HTMLResponse:
        """Every ticket the filters admit, in the order asked for."""
        project = self.backlog.project()
        selection = Selection.asked(
            project, dict(request.query_params), request.query_params.getlist("doc")
        )
        held = self.backlog.live() + (self.backlog.closed() if selection.closed else ())
        held = self._narrowed(request, held)
        if selection.deep and selection.query:
            # A deep search needs each ticket's text, which a listing does not carry, so every
            # held ticket is read in full: one knot process per ticket, only when asked for.
            held = tuple(self.backlog.ticket(one.id) for one in held)
        return self._rendered(
            request,
            "tickets.html",
            selection=selection,
            tickets=selection.ordered(
                tuple(one for one in held if selection.matches(one, project))
            ),
            counted=len(held),
        )

    def tree(self, request: Request) -> HTMLResponse:
        """What is filed under what, with each parent's progress counted."""
        return self._rendered(
            request,
            "tree.html",
            tree=Tree.over(self._narrowed(request, self.backlog.live())),
            selection=Selection(),
        )

    def queue(self, request: Request, which: str) -> HTMLResponse:
        """One of knot's own queues: what is ready to start, or what is waiting on something."""
        queues = {"ready": self.backlog.ready, "blocked": self.backlog.blocked}
        if which not in queues:
            return self._rendered(
                request,
                "unknown.html",
                looking_for=f"queue called {which}",
                selection=Selection(),
            )
        tickets = self._narrowed(request, queues[which]())
        return self._rendered(
            request,
            "queue.html",
            which=which,
            tickets=tickets,
            waves=_waves(tickets) if which == "blocked" else (),
            selection=Selection(),
        )

    def ticket(self, request: Request, identifier: str) -> HTMLResponse:
        """One ticket in full: its sections, its criteria, its graph and its notes."""
        ticket = self.backlog.ticket(identifier)
        project = self.backlog.project()
        return self._rendered(
            request,
            "ticket.html",
            ticket=ticket,
            parent=self._parent_of(ticket),
            dependencies=self.backlog.dependencies(ticket.id),
            documents=project.ordered(self._documents_of(ticket)),
            # knot checks required documents only on a move, and a closed ticket makes none.
            missing_types=project.missing_by_type(ticket) if project.is_live(ticket) else (),
            selection=Selection(),
        )

    def _documents_of(self, ticket: Ticket) -> tuple[Document, ...]:
        """A ticket's documents with their times, or as `show` stated them if knot will not list.

        Wider than `_parent_of`, which catches only a missing ticket: `show` has already read this
        ticket, so any refusal left is about its documents, and the times they would add are not
        worth a page that no longer renders.
        """
        try:
            return self.backlog.documents(ticket.id)
        except UnreadableBacklog:
            return ticket.documents

    def document(self, request: Request, identifier: str) -> HTMLResponse:
        """One document in full, with its ticket's other documents a tab away.

        The document is the one read that must succeed. Its ticket's title and its siblings are
        read after, and a ticket knot cannot find leaves the page with the bare id and the one
        document rather than a 404 about a ticket for a document knot has just shown in full.
        """
        document = self.backlog.document(identifier)
        project = self.backlog.project()
        owner, siblings = self._owner_of(document)
        body, outline = outlined(document.body) if document.body else ("", ())
        # Compared by the id knot answered with, never the one asked for: knot resolves a start
        # of an id, and the page must mark the document it resolved to.
        ordered = project.ordered(siblings or (document,))
        position = next((at for at, one in enumerate(ordered, 1) if one.id == document.id), 1)
        return self._rendered(
            request,
            "document.html",
            document=document,
            owner=owner,
            documents=ordered,
            groups=_grouped(ordered),
            position=position,
            body=body,
            outline=outline,
            selection=Selection(),
        )

    def _owner_of(self, document: Document) -> tuple[Ticket | None, tuple[Document, ...]]:
        """The ticket a document belongs to and every document it owns, or nothing of either."""
        try:
            return self.backlog.ticket(document.ticket), self.backlog.documents(document.ticket)
        except MissingTicket:
            return None, ()

    def _parent_of(self, ticket: Ticket) -> Ticket | None:
        """The ticket this one is filed under, read in full, or nothing if it names none.

        Read in full because the parent's children are what the page shows as siblings, and only
        a full read carries them. A parent that no longer exists is nothing rather than a refusal:
        the child is still worth reading, and the tree page already says it is a stray.
        """
        if not ticket.parent:
            return None
        try:
            return self.backlog.ticket(ticket.parent)
        except MissingTicket:
            return None

    def digest(self) -> str:
        """What the backlog looks like right now, as one short value the page can compare."""
        return self.backlog.digest()


# The route table, written out as data so the surface can be read in one place and asserted by
# a test. The third column is the response class, or None where the handler returns a Response
# itself; the keyword is passed only when set, because FastAPI accepts None at registration and
# fails at request time on the next handler that returns a plain value.
ROUTES: tuple[tuple[str, str, type[Response] | None], ...] = (
    ("/", "overview", HTMLResponse),
    ("/tickets", "tickets", HTMLResponse),
    ("/tree", "tree", HTMLResponse),
    ("/queue/{which}", "queue", HTMLResponse),
    ("/ticket/{identifier}", "ticket", HTMLResponse),
    ("/document/{identifier}", "document", HTMLResponse),
    ("/digest", "digest", PlainTextResponse),
    ("/tags", "tags", None),
)


def panel(backlog: Backlog) -> FastAPI:
    """The panel over one backlog.

    Built around an injected backlog rather than reaching for knot itself, which is what lets
    every page be tested against a backlog declared in a test while the real one drives a real
    project. This assembles; Pages renders.
    """
    app = FastAPI(title="knotview", docs_url=None, redoc_url=None, openapi_url=None)
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(HOSTS))
    templates = Jinja2Templates(directory=str(HERE / "templates"))
    templates.env.filters["humanise"] = _humanise
    templates.env.filters["prose"] = prose
    templates.env.filters["ago"] = _ago
    templates.env.filters["segment"] = _segment
    templates.env.tests["instant"] = _is_instant
    templates.env.globals["assets"] = _asset_stamp(HERE / "static")
    app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")
    pages = Pages(backlog, templates=templates)
    app.add_exception_handler(UnreadableBacklog, pages.unreadable)
    app.add_exception_handler(MissingTicket, pages.missing)
    app.add_exception_handler(MissingDocument, pages.missing_document)
    for path, name, response_class in ROUTES:
        chosen = {"response_class": response_class} if response_class else {}
        app.add_api_route(path, getattr(pages, name), methods=["GET"], **chosen)
    return app


def _grouped(ordered: tuple[Document, ...]) -> tuple[tuple[str, tuple[Document, ...]], ...]:
    """Documents in runs of one type, keeping the order given rather than sorting by type name.

    Jinja's own groupby sorts by the key, which would put "other" above "spec"; the order a
    project declares its types in is decided once, by `Project.ordered`, and kept here.
    """
    runs: list[tuple[str, list[Document]]] = []
    for one in ordered:
        if runs and runs[-1][0] == one.type:
            runs[-1][1].append(one)
        else:
            runs.append((one.type, [one]))
    return tuple((kind, tuple(owned)) for kind, owned in runs)


def _among(tickets: tuple[Ticket, ...], kept: set[str]) -> tuple[Ticket, ...]:
    """Those tickets whose id is among the kept ones, in the order given."""
    return tuple(one for one in tickets if one.id in kept)


def _tags(request: Request) -> Tags:
    """The tags the reader's cookie carries."""
    return Tags.from_cookie(request.cookies.get(COOKIE))


def _waves(tickets: tuple[Ticket, ...]) -> tuple[tuple[int | None, tuple[Ticket, ...]], ...]:
    """The blocked tickets grouped by knot's level: the rounds of closing before each can start.

    Level 1 becomes ready once today's ready tickets close, level 2 after those, and so on, which
    is what makes the blocked queue a schedule rather than a list. A level knot gives as null is
    a ticket on a dependency cycle, which no schedule reaches; it goes last, under its own name.
    """
    known = sorted({t.level for t in tickets if t.level is not None})
    levels: list[int | None] = [*known, *([None] if any(t.level is None for t in tickets) else [])]
    return tuple((level, tuple(t for t in tickets if t.level == level)) for level in levels)


def _asset_stamp(folder: Path) -> str:
    """A short digest of the static files, put on their URLs so a browser fetches new ones.

    The static files are served with no cache policy, so a browser keeps them by heuristic and a
    reader who restarts the panel after an upgrade can keep last month's script under this
    month's markup. A stamp that moves with the contents makes each version a new URL.
    """
    digest = hashlib.sha256()
    for path in sorted(one for one in folder.rglob("*") if one.is_file()):
        digest.update(str(path.relative_to(folder)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()[:12]


def _is_instant(stamped: str | None) -> bool:
    """Whether a value is an instant knot wrote: a full date and time, in UTC, marked with a Z.

    A note's heading is whatever stood in bold above it, and by hand that can be a bare date or a
    word. Labelling "2026-09-12" as UTC and letting the browser restate it would invent a time of
    day the note never had, and an instant carrying an offset would be mislabelled UTC. Only what
    passes here becomes a time element; anything else is shown as written.
    """
    if not stamped or not stamped.endswith("Z") or "T" not in stamped:
        return False
    try:
        datetime.fromisoformat(stamped.replace("Z", "+00:00"))
    except ValueError:
        return False
    return True


def _ago(stamped: str | None, now: datetime | None = None) -> str:
    """An instant as a distance from now, which is how a reader following an agent reads it.

    Coarse on purpose: minutes within the hour, hours within the day, then days. The exact instant
    is one hover away on the same element.
    """
    if not stamped:
        return "—"
    try:
        then = datetime.fromisoformat(stamped.replace("Z", "+00:00"))
    except ValueError:
        return stamped
    passed = (now or datetime.now(UTC)) - then
    minutes = int(passed.total_seconds() // 60)
    if minutes < 1:
        return "just now"
    if minutes < 60:
        return f"{minutes} min ago"
    if minutes < 60 * 24:
        return f"{minutes // 60} h ago"
    return f"{minutes // (60 * 24)} d ago"


def _segment(identifier: str) -> str:
    """An id made safe as one path segment, slashes included, which Jinja's urlencode keeps.

    knot writes ids it makes from safe characters, but reads whatever a hand-edited file names,
    and an id with a `#`, `?` or `/` in it would otherwise link somewhere other than itself.
    """
    return quote(identifier, safe="")


def _humanise(stamped: str | None) -> str:
    """An instant as a reader scans it: the date, then the time, without the microseconds.

    knot writes an ISO instant to the microsecond, which is the right thing to store and the wrong
    thing to put in a table: the digits that differ between two tickets updated in the same minute
    are the ones nobody reads.
    """
    if not stamped:
        return "—"
    return stamped.replace("T", " ")[:16].replace("Z", "")
