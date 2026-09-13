"""The panel: every route a GET, every answer a page or a stream."""

import asyncio
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from knotview.panel.overview import Overview
from knotview.panel.selection import ANY, ORDERS, Selection
from knotview.panel.tree import Tree
from knotview.reading.backlog import Backlog
from knotview.reading.snapshot import Snapshot
from knotview.values.unreadable_backlog import UnreadableBacklog

HERE = Path(__file__).resolve().parent

# How often the live stream looks for a change. A backlog is edited by somebody's agent a few times
# a minute at most, and the check is a directory walk over small files, so a second is responsive
# without being a busy loop. The stream sends the digest rather than the data: the page asks for
# what it needs, which keeps one code path for rendering whether a reader arrived or refreshed.
HEARTBEAT = 1.0

# What the stream sends when nothing has changed, so a proxy or a sleeping laptop does not decide
# the connection is dead. A comment line is the server-sent-events way of saying nothing.
KEEPALIVE = ": waiting\n\n"


def panel(backlog: Backlog, *, heartbeat: float = HEARTBEAT) -> FastAPI:
    """The panel over one backlog.

    Built around an injected backlog rather than reaching for knot itself, which is what lets every
    page be tested against a backlog declared in a test while the real one drives a real project.

    Read-only, and structurally so: every route below is a GET, there is no form, and the backlog
    port has no method that writes. The backlog stays driven by whatever writes it, and this
    watches.
    """
    app = FastAPI(title="knotview", docs_url=None, redoc_url=None, openapi_url=None)
    pages = Jinja2Templates(directory=str(HERE / "templates"))
    pages.env.filters["humanise"] = _humanise
    app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")

    def rendered(request: Request, template: str, **context: object) -> HTMLResponse:
        """One page, with what every page needs already in it."""
        project = backlog.project()
        return pages.TemplateResponse(
            request=request,
            name=template,
            context={"project": project, "orders": ORDERS, "any": ANY, **context},
        )

    @app.exception_handler(UnreadableBacklog)
    async def unreadable(request: Request, refusal: UnreadableBacklog) -> HTMLResponse:
        """Say what could not be read and what to do about it, rather than a stack trace.

        A panel pointed at the wrong directory is the ordinary first mistake, and the page that
        admits
        it is worth more than the one that works once everything is right.
        """
        return pages.TemplateResponse(
            request=request,
            name="unreadable.html",
            context={"refusal": refusal},
            status_code=503,
        )

    @app.get("/", response_class=HTMLResponse)
    async def overview(request: Request) -> HTMLResponse:
        """The backlog counted by type, by status and by priority, with the queues beside it."""
        return rendered(
            request,
            "overview.html",
            overview=Overview.over(Snapshot.read(backlog)),
            selection=Selection(),
        )

    @app.get("/tickets", response_class=HTMLResponse)
    async def tickets(request: Request) -> HTMLResponse:
        """Every ticket the filters admit, in the order asked for."""
        project = backlog.project()
        selection = Selection.asked(project, dict(request.query_params))
        held = backlog.live() + (backlog.closed() if selection.closed else ())
        return rendered(
            request,
            "tickets.html",
            selection=selection,
            tickets=selection.ordered(tuple(one for one in held if selection.matches(one))),
            counted=len(held),
        )

    @app.get("/tree", response_class=HTMLResponse)
    async def tree(request: Request) -> HTMLResponse:
        """What is filed under what, with each parent's progress counted."""
        project = backlog.project()
        return rendered(
            request,
            "tree.html",
            tree=Tree.over(backlog.live(), terminal=project.terminal_statuses),
            selection=Selection(),
        )

    @app.get("/queue/{which}", response_class=HTMLResponse)
    async def queue(request: Request, which: str) -> HTMLResponse:
        """One of knot's own queues: what is ready to start, or what is waiting on something."""
        queues = {"ready": backlog.ready, "blocked": backlog.blocked}
        if which not in queues:
            return rendered(
                request,
                "unknown.html",
                looking_for=f"a queue called {which}",
                selection=Selection(),
            )
        return rendered(
            request,
            "queue.html",
            which=which,
            tickets=queues[which](),
            selection=Selection(),
        )

    @app.get("/ticket/{identifier}", response_class=HTMLResponse)
    async def ticket(request: Request, identifier: str) -> HTMLResponse:
        """One ticket in full: its sections, its criteria, its graph and its notes."""
        return rendered(
            request, "ticket.html", ticket=backlog.ticket(identifier), selection=Selection()
        )

    @app.get("/digest", response_class=PlainTextResponse)
    async def digest() -> str:
        """What the backlog looks like right now, as one short value the page can compare."""
        return backlog.digest()

    @app.get("/live")
    async def live() -> StreamingResponse:
        """A one-way stream that says when the backlog changed, and never what to do about it.

        One direction by construction: a stream that cannot carry a command keeps the read-only
        guarantee structural rather than conventional. It sends the digest, and the page decides to
        reload; the server never pushes markup, so there is one rendering path whether a reader
        arrived, refreshed, or was told something moved.
        """
        return StreamingResponse(
            _changes(backlog, heartbeat),
            media_type="text/event-stream",
            headers={"cache-control": "no-store", "x-accel-buffering": "no"},
        )

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


def _humanise(stamped: str | None) -> str:
    """An instant as a reader scans it: the date, then the time, without the microseconds.

    knot writes an ISO instant to the microsecond, which is the right thing to store and the wrong
    thing to put in a table: the digits that differ between two tickets updated in the same minute
    are the ones nobody reads.
    """
    if not stamped:
        return "—"
    return stamped.replace("T", " ")[:16].replace("Z", "")
