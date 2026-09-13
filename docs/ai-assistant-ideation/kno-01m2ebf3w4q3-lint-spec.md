# kno-01m2ebf3w4q3 — Lint: `panel()` as assembly over a `Pages` class, and the value objects' attribute counts

## Changes Since Last Cycle

- The `response_class=None` paragraph had the hazard backwards: registration accepts `None`;
  the failure is at request time, and only when a handler returns a non-Response value. The
  code block now shows the conditional form and the paragraph states the latent hazard
  (findings 32, 33).

Spec. Story kno-01m2ebf3w4q3. Brainstorm:
`docs/ai-assistant-ideation/kno-01m2ebf3w4q3-lint-brainstorm.md`. Date: 2026-09-13.

## Problem

Four lint findings fail the pre-commit hooks on any commit that touches their files, so those
files cannot be changed without `--no-verify`:

| finding | where | measured |
|---|---|---|
| ruff C901, pylint R1260 | `src/knotview/panel/app.py` `panel()` | McCabe 11, limit 8 |
| pylint R0902 | `src/knotview/values/ticket.py` `Ticket` | 20 attributes, limit 7 |
| pylint R0902 | `src/knotview/values/project.py` `Project` | 12 |
| pylint R0902 | `src/knotview/panel/selection.py` `Selection` | 9 |

`panel()`'s 11 is 1 plus nine nested `def`s plus one `if`; it has one path. Carried from
kno-01m2ebf3c8mx: the unknown-queue page renders "This panel has no a queue called X", pinned by
`tests/panel/test_queue.py`; and `Project.is_terminal` has no caller (tree.html tests membership
in `project.terminal_statuses` directly).

## Goal

1. `ruff check src tests` and `pylint src tests` report nothing, so every file commits through
   the hooks without `--no-verify`.
2. No URL, template, response class or rendered text changes except the unknown-queue sentence.
3. The route surface is asserted by a test that exists before the refactor.
4. `pytest` stays at 100 percent line and branch coverage.

## Out of scope

Splitting `Ticket`, `Project` or `Selection` into nested values; raising `max-attributes`
project-wide; any change to `_changes`, `_humanise`, the templates or the static files.

## Design

### The route-surface test, first

`tests/panel/test_routes.py`, committed before any source change:

- `test_the_route_table_is_exactly_these_paths`: the set of `route.path` over `app.routes`
  equals `{"/static", "/", "/tickets", "/tree", "/queue/{which}", "/ticket/{identifier}",
  "/digest", "/live"}`.
- `test_every_route_is_a_get`: for every `fastapi.routing.APIRoute` in `app.routes`,
  `route.methods == {"GET"}`. The `/static` entry is a `starlette.routing.Mount` and is covered
  by the path assertion only.
- `test_pages_answer_as_html_and_the_digest_as_text`, parametrised over `/`, `/tickets`,
  `/tree`, `/queue/ready`, `/ticket/pro-01m2aaaaaaaa`: the content-type starts with
  `text/html`; and `/digest` starts with `text/plain`.

### `Pages`

In `src/knotview/panel/app.py`:

```python
class Pages:
    """Every page the panel serves, over one backlog.

    A class rather than a set of closures so that which backlog a page reads is a named
    attribute, and so that assembling the app (mounting static files, registering the
    exception handler, writing out the route table) is separate from rendering a page.
    """

    def __init__(self, backlog: Backlog, *, templates: Jinja2Templates, heartbeat: float) -> None:
        self.backlog = backlog
        self.templates = templates
        self.heartbeat = heartbeat

    def rendered(self, request: Request, template: str, **context: object) -> HTMLResponse: ...
    async def unreadable(self, request: Request, refusal: UnreadableBacklog) -> HTMLResponse: ...
    async def overview(self, request: Request) -> HTMLResponse: ...
    async def tickets(self, request: Request) -> HTMLResponse: ...
    async def tree(self, request: Request) -> HTMLResponse: ...
    async def queue(self, request: Request, which: str) -> HTMLResponse: ...
    async def ticket(self, request: Request, identifier: str) -> HTMLResponse: ...
    async def digest(self) -> str: ...
    async def live(self) -> StreamingResponse: ...
```

Each method body is the existing handler's body with `backlog` and `pages` read from `self`.
`queue` passes `looking_for=f"queue called {which}"`.

`panel()` becomes:

```python
ROUTES = (
    ("/", "overview", HTMLResponse),
    ("/tickets", "tickets", HTMLResponse),
    ("/tree", "tree", HTMLResponse),
    ("/queue/{which}", "queue", HTMLResponse),
    ("/ticket/{identifier}", "ticket", HTMLResponse),
    ("/digest", "digest", PlainTextResponse),
    ("/live", "live", None),
)


def panel(backlog: Backlog, *, heartbeat: float = HEARTBEAT) -> FastAPI:
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

The conditional is deliberate. `add_api_route` accepts `response_class=None` at registration,
and `/live` would even work with it, because a handler that returns a `Response` directly
(its `StreamingResponse`) never reaches the response-class call. The hazard is latent: the
next `None` row whose handler returns a plain value fails at request time with a `TypeError`
from inside FastAPI's routing. Passing the keyword only when set leaves FastAPI's default in
place for `/live`, exactly as the decorator form does today. `panel()` then has one loop and no
nested defs: McCabe 2, measured on a prototype with the limit forced to 1; the conditional
expression adds no point. The docstrings on `panel()` and on
the handlers move with them unchanged in substance.

### The value objects

Per-class disables, the reason in the docstring:

- `Ticket`, `Project`: `# pylint: disable=too-many-instance-attributes` on the class line, with a
  docstring sentence: the fields are knot's record shape, and grouping them into nested values
  would hide the schema this reader mirrors.
- `Selection`: the same disable with its own sentence: the fields are the query string the panel
  defines, one per filter the URL carries, and `query_string` and `matches` read them in one
  place.

No change to `pyproject.toml`.

### `is_terminal`

`Project.is_terminal` and `tests/values/test_project.py::test_a_status_is_terminal_when_the_project_says_so`
are deleted. `pylint src/knotview/values/project.py` is run after the deletion; the result is
recorded in the execution report. If `R0903` fires (it should not: a method-less frozen
dataclass measured clean on a synthetic file), a docstring-reasoned disable is the fallback.

### The sentence

`tests/panel/test_queue.py` asserts `"This panel has no queue called soon."` in the same commit
as the `Pages` refactor; the assertion is updated, not loosened.

## Acceptance criteria

1. `devenv shell -- ruff check src tests` prints "All checks passed".
2. `devenv shell -- pylint src tests` reports no messages.
3. `devenv shell -- pytest` exits zero at 100 percent line and branch coverage.
4. `git log --oneline` shows the route-surface test commit before the refactor commit.
5. `tests/panel/test_routes.py` asserts the exact path set, `methods == {"GET"}` for every
   `APIRoute`, and the content-types.
6. The unknown-queue page renders "This panel has no queue called soon.", asserted in
   `tests/panel/test_queue.py`.
7. `grep -rn is_terminal src tests` is empty.
8. `git diff main -- src/knotview/panel/templates src/knotview/panel/static pyproject.toml`
   is empty.

## Testing strategy

The existing page tests assert rendered content over a declared backlog and stay unchanged
except the one sentence; the route-surface test guards the surface; verify-work runs the full
suite and the hooks.

## Cross-story collision check

No `_references/project/` high-risk-surfaces doc is present, and the repository has no open pull
requests and no remote, so no collision scan applies. No collision found.
