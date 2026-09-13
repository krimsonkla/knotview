# kno-01m2ebf3w4q3 Lint Implementation Plan

**Goal:** `ruff check src tests` and `pylint src tests` report nothing, with no change to any
URL, template, response class or rendered text except the unknown-queue sentence, and the suite
still at 100 percent.

**Architecture:** A `Pages` class in `src/knotview/panel/app.py` holds the backlog, the
templates and the heartbeat with one method per page; `panel()` assembles the app from a
`ROUTES` table. The three value objects keep their shape and carry a per-class pylint disable
with the reason in the docstring. `Project.is_terminal` is deleted. A route-surface test lands
before any of it.

**Tech Stack:** Python 3.12, FastAPI 0.141, pytest with 100 percent fail-under, ruff C901 at 8,
pylint with the mccabe extension.

Spec: `docs/ai-assistant-ideation/kno-01m2ebf3w4q3-lint-spec.md`. Run every command from the
repo root through `devenv shell -- <cmd>`. Conventional commit messages, no trailers. If a hook
rewrites a file, re-stage and commit again.

---

## File map

Create: `tests/panel/test_routes.py`.
Modify: `src/knotview/panel/app.py` (whole module below the constants), `src/knotview/values/ticket.py:10`,
`src/knotview/values/project.py:7-46`, `src/knotview/panel/selection.py:18`,
`tests/panel/test_queue.py:14`, `tests/values/test_project.py:14-15`.

---

### Task 1: The route-surface test, before anything moves

**Files:**
- Create: `tests/panel/test_routes.py`

- [ ] **Step 1: Write the test**

```python
"""The panel's surface: which paths exist, that every one is a GET, and what they answer with."""

import pytest
from fastapi.routing import APIRoute

from knotview.panel.app import panel
from tests.panel.declared import DeclaredBacklog

PATHS = {
    "/static",
    "/",
    "/tickets",
    "/tree",
    "/queue/{which}",
    "/ticket/{identifier}",
    "/digest",
    "/live",
}


def test_the_route_table_is_exactly_these_paths():
    assert {route.path for route in panel(DeclaredBacklog()).routes} == PATHS


def test_every_route_is_a_get():
    """The read-only guarantee at the HTTP surface. /static is a Mount with no methods and is
    covered by the path assertion above."""
    routes = [route for route in panel(DeclaredBacklog()).routes if isinstance(route, APIRoute)]

    assert len(routes) == 7
    assert all(route.methods == {"GET"} for route in routes)


@pytest.mark.parametrize(
    "path", ["/", "/tickets", "/tree", "/queue/ready", "/ticket/pro-01m2aaaaaaaa"]
)
def test_pages_answer_as_html(client, path):
    assert client(DeclaredBacklog()).get(path).headers["content-type"].startswith("text/html")


def test_the_digest_answers_as_text(client):
    response = client(DeclaredBacklog()).get("/digest")

    assert response.headers["content-type"].startswith("text/plain")
```

- [ ] **Step 2: Run it against the current app**

Run: `devenv shell -- pytest tests/panel/test_routes.py -q --no-cov`
Expected: 8 passed. This is the safety net; it must be green before the refactor.

- [ ] **Step 3: Commit**

`git add tests/panel/test_routes.py && git commit -m "test(panel): pin the route surface before the refactor"`

---

### Task 2: `Pages`, and `panel()` as assembly

**Files:**
- Modify: `src/knotview/panel/app.py` from the `panel` definition to the end of `_changes`
- Modify: `tests/panel/test_queue.py:14`

- [ ] **Step 1: Update the sentence assertion first, so it fails**

In `tests/panel/test_queue.py` replace the two comment lines and the assertion with:
```python
    assert "This panel has no queue called soon." in response.text
```
Run: `devenv shell -- pytest tests/panel/test_queue.py -q --no-cov`
Expected: 1 failed (the old wording), 1 passed.

- [ ] **Step 2: Replace `panel()` and the nested handlers**

Replace everything from `def panel(` through the end of the `return app` line with:

```python
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

    def rendered(self, request: Request, template: str, **context: object) -> HTMLResponse:
        """One page, with what every page needs already in it."""
        project = self.backlog.project()
        return self.templates.TemplateResponse(
            request=request,
            name=template,
            context={"project": project, "orders": ORDERS, "any": ANY, **context},
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
        """The backlog counted by type, by status and by priority, with the queues beside it."""
        return self.rendered(
            request,
            "overview.html",
            overview=Overview.over(Snapshot.read(self.backlog)),
            selection=Selection(),
        )

    async def tickets(self, request: Request) -> HTMLResponse:
        """Every ticket the filters admit, in the order asked for."""
        project = self.backlog.project()
        selection = Selection.asked(project, dict(request.query_params))
        held = self.backlog.live() + (self.backlog.closed() if selection.closed else ())
        return self.rendered(
            request,
            "tickets.html",
            selection=selection,
            tickets=selection.ordered(tuple(one for one in held if selection.matches(one))),
            counted=len(held),
        )

    async def tree(self, request: Request) -> HTMLResponse:
        """What is filed under what, with each parent's progress counted."""
        project = self.backlog.project()
        return self.rendered(
            request,
            "tree.html",
            tree=Tree.over(self.backlog.live(), terminal=project.terminal_statuses),
            selection=Selection(),
        )

    async def queue(self, request: Request, which: str) -> HTMLResponse:
        """One of knot's own queues: what is ready to start, or what is waiting on something."""
        queues = {"ready": self.backlog.ready, "blocked": self.backlog.blocked}
        if which not in queues:
            return self.rendered(
                request,
                "unknown.html",
                looking_for=f"queue called {which}",
                selection=Selection(),
            )
        return self.rendered(
            request,
            "queue.html",
            which=which,
            tickets=queues[which](),
            selection=Selection(),
        )

    async def ticket(self, request: Request, identifier: str) -> HTMLResponse:
        """One ticket in full: its sections, its criteria, its graph and its notes."""
        return self.rendered(
            request,
            "ticket.html",
            ticket=self.backlog.ticket(identifier),
            selection=Selection(),
        )

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


# The route table, written out as data so the surface can be read in one place and asserted
# by a test. The third column is the response class, or None where the handler returns a
# Response itself; the keyword is passed only when set, because FastAPI accepts None at
# registration and fails at request time on the next handler that returns a plain value.
ROUTES: tuple[tuple[str, str, type[Response] | None], ...] = (
    ("/", "overview", HTMLResponse),
    ("/tickets", "tickets", HTMLResponse),
    ("/tree", "tree", HTMLResponse),
    ("/queue/{which}", "queue", HTMLResponse),
    ("/ticket/{identifier}", "ticket", HTMLResponse),
    ("/digest", "digest", PlainTextResponse),
    ("/live", "live", None),
)


def panel(backlog: Backlog, *, heartbeat: float = HEARTBEAT) -> FastAPI:
    """The panel over one backlog.

    Built around an injected backlog rather than reaching for knot itself, which is what lets
    every page be tested against a backlog declared in a test while the real one drives a real
    project. This assembles; Pages renders.
    """
    app = FastAPI(title="knotview", docs_url=None, redoc_url=None, openapi_url=None)
    templates = Jinja2Templates(directory=str(HERE / "templates"))
    templates.env.filters["humanise"] = _humanise
    app.mount("/static", StaticFiles(directory=str(HERE / "static")), name="static")
    pages = Pages(backlog, templates=templates, heartbeat=heartbeat)
    app.add_exception_handler(UnreadableBacklog, pages.unreadable)
    for path, name, response_class in ROUTES:
        chosen = {"response_class": response_class} if response_class else {}
        app.add_api_route(path, getattr(pages, name), methods=["GET"], **chosen)
    return app
```

Add `Response` to the `fastapi.responses` import line:
```python
from fastapi.responses import HTMLResponse, PlainTextResponse, Response, StreamingResponse
```
Leave `_changes` and `_humanise` as they are. The module docstring and the constants above
`panel` are unchanged.

- [ ] **Step 3: Run the panel tests and the linters on the file**

Run: `devenv shell -- pytest tests/panel -q --no-cov`
Expected: all pass, including `test_routes.py` and the updated queue sentence.
Run: `devenv shell -- ruff check src/knotview/panel/app.py && devenv shell -- pylint src/knotview/panel/app.py`
Expected: no C901, no R1260. If pylint reports `too-few-public-methods` or `too-many-public-methods`
on `Pages`, it has nine public methods and the project's `min-public-methods` is 1, so neither
should fire; report any other message rather than disabling it.

- [ ] **Step 4: Commit**

`git add src/knotview/panel/app.py tests/panel/test_queue.py && git commit -m "refactor(panel): pages as a class, panel() as assembly, and a grammatical unknown-queue page"`

---

### Task 3: The value objects' attribute counts

**Files:**
- Modify: `src/knotview/values/ticket.py:10`, `src/knotview/values/project.py:7`,
  `src/knotview/panel/selection.py:18`

- [ ] **Step 1: Ticket**

Change the class line and append one sentence to the end of the docstring:
```python
@dataclass(frozen=True, kw_only=True)
class Ticket:  # pylint: disable=too-many-instance-attributes
```
and, as the docstring's last paragraph:
```
    It holds more attributes than the linter's default allows because the fields are knot's
    record shape; grouping them into nested values would hide the schema this reader mirrors.
```

- [ ] **Step 2: Project**

```python
@dataclass(frozen=True, kw_only=True)
class Project:  # pylint: disable=too-many-instance-attributes
```
with the same closing paragraph, worded for knot's project configuration:
```
    It holds more attributes than the linter's default allows because the fields are what knot
    info reports; grouping them into nested values would hide the configuration this panel
    mirrors.
```

- [ ] **Step 3: Selection**

```python
@dataclass(frozen=True, kw_only=True)
class Selection:  # pylint: disable=too-many-instance-attributes
```
with its own reason:
```
    It holds more attributes than the linter's default allows because the fields are the query
    string this panel defines, one per filter the URL carries, and query_string and matches
    read them in one place; a split would move the filter list away from the code that keeps
    every link honest.
```

- [ ] **Step 4: Lint and test**

Run: `devenv shell -- pylint src/knotview/values/ticket.py src/knotview/values/project.py src/knotview/panel/selection.py`
Expected: no messages.
Run: `devenv shell -- pytest tests/values tests/panel -q --no-cov`
Expected: all pass.

- [ ] **Step 5: Commit**

`git add src/knotview/values/ticket.py src/knotview/values/project.py src/knotview/panel/selection.py && git commit -m "chore(values): record why the three records exceed the attribute limit"`

---

### Task 4: Delete `is_terminal`

**Files:**
- Modify: `src/knotview/values/project.py` (remove the `is_terminal` method)
- Modify: `tests/values/test_project.py` (remove `test_a_status_is_terminal_when_the_project_says_so`)

- [ ] **Step 1: Delete the method and its test**

Remove from `project.py`:
```python
    def is_terminal(self, status: str) -> bool:
        """Whether that status means a ticket is done with, whatever the project calls it."""
        return status in self.terminal_statuses
```
Remove from `test_project.py` the last test function (two lines plus its blank lines).

- [ ] **Step 2: Confirm the dataclass exemption on the real file**

Run: `devenv shell -- pylint src/knotview/values/project.py`
Expected: no messages. Record the output line in the execution report. If `R0903`
(too-few-public-methods) fires, add `# pylint: disable=too-few-public-methods` to the class
line with a docstring sentence saying the record has no behaviour of its own; do not reinstate
the method.

- [ ] **Step 3: Confirm nothing references it**

Run: `grep -rn is_terminal src tests`
Expected: no output.

- [ ] **Step 4: Commit**

`git add src/knotview/values/project.py tests/values/test_project.py && git commit -m "refactor(values): drop the uncalled is_terminal"`

---

### Task 5: The gate

- [ ] **Step 1**: `devenv shell -- ruff check src tests` → "All checks passed!"
- [ ] **Step 2**: `devenv shell -- pylint src tests` → no messages, rated 10.00.
- [ ] **Step 3**: `devenv shell -- pytest` → all pass, `TOTAL ... 100%`.
- [ ] **Step 4**: `git diff main -- src/knotview/panel/templates src/knotview/panel/static pyproject.toml` → empty.
- [ ] **Step 5**: `grep -rn "pragma: no cover" src tests` → empty.
- [ ] **Step 6**: nothing to commit if all green; otherwise fix and commit under `test:` or `refactor:`.
