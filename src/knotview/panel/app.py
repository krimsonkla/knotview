"""The panel: every route a GET, every answer a page or a stream."""

import asyncio
import hashlib
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import (
    HTMLResponse,
    PlainTextResponse,
    RedirectResponse,
    Response,
    StreamingResponse,
)
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.trustedhost import TrustedHostMiddleware

from knotview.panel.overview import Overview
from knotview.panel.prose import rendered as prose
from knotview.panel.selection import ANY, ORDERS, Selection
from knotview.panel.tags import COOKIE, Tags
from knotview.panel.tree import Tree
from knotview.reading.backlog import Backlog
from knotview.reading.snapshot import Snapshot
from knotview.values.missing_ticket import MissingTicket
from knotview.values.ticket import Ticket
from knotview.values.unreadable_backlog import UnreadableBacklog

HERE = Path(__file__).resolve().parent

# How often the live stream looks for a change. A backlog is edited by somebody's agent a few times
# a minute at most, and the check is a directory walk over small files, so a second is responsive
# without being a busy loop. The stream sends the digest rather than the data: the page asks for
# what it needs, which keeps one code path for rendering whether a reader arrived or refreshed.
HEARTBEAT = 1.0

# The names a browser may address the panel by. It binds loopback, but a page on any other site
# can still make a browser send requests to a loopback port under that site's own host name, and
# the backlog would answer; refusing every host but these closes that door.
HOSTS = ("127.0.0.1", "localhost", "[::1]")

# What the stream sends when nothing has changed, so a proxy or a sleeping laptop does not decide
# the connection is dead. A comment line is the server-sent-events way of saying nothing.
KEEPALIVE = ": waiting\n\n"


class Pages:
    """Every page the panel serves, over one backlog.

    A class rather than a set of closures so that which backlog a page reads is a named
    attribute, and so that assembling the app (mounting the static files, registering the
    exception handler, writing out the route table) is separate from rendering a page.

    Read-only, and structurally so: every route in ROUTES is a GET, there is no form, and the
    backlog port has no method that writes. The backlog stays driven by whatever writes it, and
    this watches.
    """

    def __init__(self, backlog: Backlog, *, templates: Jinja2Templates, heartbeat: float) -> None:
        self.backlog = backlog
        self.templates = templates
        self.heartbeat = heartbeat

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

    async def tags(
        self, request: Request, add: str = "", drop: str = "", clear: str = ""
    ) -> Response:
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

    async def missing(self, request: Request, refusal: MissingTicket) -> HTMLResponse:
        """The page for a ticket that is not there: a 404 offering the list, not a 503."""
        return self._rendered(
            request,
            "unknown.html",
            status=404,
            looking_for=f"ticket called {refusal.identifier}",
            selection=Selection(),
        )

    async def unreadable(self, request: Request, refusal: UnreadableBacklog) -> HTMLResponse:
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

    async def overview(self, request: Request) -> HTMLResponse:
        """The backlog counted by type, by status and by priority, with the queues beside it.

        The overview carries the reader's selection through its links, so arriving from a filtered
        list and clicking a card narrows further instead of starting over.
        """
        project = self.backlog.project()
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
            selection=Selection.asked(project, dict(request.query_params)),
        )

    async def tickets(self, request: Request) -> HTMLResponse:
        """Every ticket the filters admit, in the order asked for."""
        project = self.backlog.project()
        selection = Selection.asked(project, dict(request.query_params))
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
            tickets=selection.ordered(tuple(one for one in held if selection.matches(one))),
            counted=len(held),
        )

    async def tree(self, request: Request) -> HTMLResponse:
        """What is filed under what, with each parent's progress counted."""
        return self._rendered(
            request,
            "tree.html",
            tree=Tree.over(self._narrowed(request, self.backlog.live())),
            selection=Selection(),
        )

    async def queue(self, request: Request, which: str) -> HTMLResponse:
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

    async def ticket(self, request: Request, identifier: str) -> HTMLResponse:
        """One ticket in full: its sections, its criteria, its graph and its notes."""
        ticket = self.backlog.ticket(identifier)
        return self._rendered(
            request,
            "ticket.html",
            ticket=ticket,
            parent=self._parent_of(ticket),
            dependencies=self.backlog.dependencies(ticket.id),
            selection=Selection(),
        )

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

    async def digest(self) -> str:
        """What the backlog looks like right now, as one short value the page can compare."""
        return self.backlog.digest()

    async def live(self) -> StreamingResponse:
        """A one-way stream that says when the backlog changed, and never what to do about it.

        One direction by construction: a stream that cannot carry a command keeps the read-only
        guarantee structural rather than conventional. It sends the digest, and the page decides
        to reload; the server never pushes markup, so there is one rendering path whether a
        reader arrived, refreshed, or was told something moved.
        """
        return StreamingResponse(
            _changes(self.backlog, self.heartbeat),
            media_type="text/event-stream",
            headers={"cache-control": "no-store", "x-accel-buffering": "no"},
        )


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
    ("/digest", "digest", PlainTextResponse),
    ("/live", "live", None),
    ("/tags", "tags", None),
)


def panel(backlog: Backlog, *, heartbeat: float = HEARTBEAT) -> FastAPI:
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
    templates.env.tests["instant"] = _is_instant
    templates.env.globals["assets"] = _asset_stamp(HERE / "static")
    app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")
    pages = Pages(backlog, templates=templates, heartbeat=heartbeat)
    app.add_exception_handler(UnreadableBacklog, pages.unreadable)
    app.add_exception_handler(MissingTicket, pages.missing)
    for path, name, response_class in ROUTES:
        chosen = {"response_class": response_class} if response_class else {}
        app.add_api_route(path, getattr(pages, name), methods=["GET"], **chosen)
    return app


async def _changes(backlog: Backlog, heartbeat: float):
    """Yield an event whenever the backlog's digest moves, and a comment while it does not."""
    last = None
    while True:
        try:
            current = backlog.digest()
        except UnreadableBacklog as refusal:
            yield f"event: unreadable\ndata: {refusal.message}\n\n"
            return
        if current != last:
            last = current
            yield f"event: changed\ndata: {current}\n\n"
        else:
            yield KEEPALIVE
        await asyncio.sleep(heartbeat)


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


def _humanise(stamped: str | None) -> str:
    """An instant as a reader scans it: the date, then the time, without the microseconds.

    knot writes an ISO instant to the microsecond, which is the right thing to store and the wrong
    thing to put in a table: the digits that differ between two tickets updated in the same minute
    are the ones nobody reads.
    """
    if not stamped:
        return "—"
    return stamped.replace("T", " ")[:16].replace("Z", "")
