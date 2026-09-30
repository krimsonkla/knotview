# knotview

> This file is maintained by AI assistants. Keep it up to date as the project evolves.

## Tech Stack

- **Languages**: Python 3.12
- **Frameworks**: FastAPI with Jinja2 templates, served by uvicorn
- **Infrastructure**: none; the panel binds loopback on one machine
- **Testing**: pytest with pytest-cov, 100 percent line and branch gate
- **Package Manager**: uv (`uv.lock` is committed; `pip install .` also works)
- **Dev Environment**: the maintainer uses devenv.sh with hooks from a private layer; contributors
  use `uv sync --all-groups` and the commands in CONTRIBUTING.md

## Project Structure

- `src/knotview/entry/` the `knotview` command and the saved-projects file
- `src/knotview/reading/` the `Backlog` port, its one implementation over `knot ... --json`, and
  the envelope reader
- `src/knotview/panel/` the FastAPI app (`Pages` and `panel()`), the selection, tree and overview
  values, the templates and the static files
- `src/knotview/values/` frozen dataclasses: Ticket, Project, Criterion, Reference, and the two
  refusals
- `tests/` mirrors `src/`; `tests/reading/envelopes/` holds JSON recorded from knot 0.15.0
- `.tickets/docs/` each ticket's attached knot documents, including its brainstorm, spec and plan
- `.tickets/` this project's own knot backlog, which is also the fixture it is developed against

## Build & Test

```bash
uv sync --all-groups
uv run pytest                    # whole suite with the coverage gate
uv run pytest --no-cov <path>    # a subset, without the gate
uv run ruff check src tests && uv run black --check src tests && uv run pylint src tests
```

Inside the maintainer's devenv shell the same tools run as commit hooks through `prek`
(`prek run --all-files`); there is no `pre-commit` binary. Commit messages are
`<type>(<scope>): <description>`, and the hooks reject `Co-Authored-By` and attribution trailers.

## Architecture

The panel reads a knot backlog and renders pages; it never writes a ticket. `KnotCommand` runs
`knot <read-verb> --json` in the project directory and hands the envelope to `knot_envelope`,
which turns knot's JSON into the value types. It never parses `.tickets/` itself: knot owns that
schema, and a second parser would drift on the first release that adds a field. `Backlog` is the
port the panel is written against; tests use a `DeclaredBacklog` over tuples so every page is
asserted without a process.

`panel(backlog)` assembles the FastAPI app from a `ROUTES` table over a `Pages` object, one
method per page. Every route is a GET, `READS` is disjoint from knot's write verbs, and only
`reading/knot_command.py` may start a process; tests assert all three. Each open page asks
`/digest` about once a second (not while hidden) for a digest of the ticket and document files'
names and modification times, and reloads itself when it changes. It polls rather than holding a
stream, because a browser allows six connections to one host and a stream per tab exhausted them.
Page handlers, the refusal pages' included, are plain functions, so their knot reads run in the
thread pool; the backlog is therefore read from several threads at once, and anything a reader
caches must be safe to compute concurrently (`KnotCommand` locks its one cached value). A hidden
tab stops polling after its first answer and asks again as soon as it is shown; a panel that
stops answering is asked less often, up to twice a minute.

## Key Files

- `src/knotview/reading/knot_command.py`: `READS`, `_spoken` (argv with `--json --`), the
  check-aware `integrity`, and the digest.
- `src/knotview/reading/knot_envelope.py`: `answered` and `verdict` (knot's `check` co-emits
  `ok: false` with data), `ticket_from`, `project_from`.
- `src/knotview/panel/app.py`: `Pages`, `ROUTES`, `panel()`, `HOSTS`.
- `src/knotview/panel/static/follow.js`: the digest poll, the since-last-looked marks, local time.
- `src/knotview/panel/selection.py`: every filter the URL carries, and the query-string builder.
- `src/knotview/panel/tags.py`: the sticky tag choice, its cookie, and `narrow`.
- `tests/reading/conftest.py`: the fake `knot` script the reading tests drive.
- `tests/reading/record_envelopes.py`: regenerates the recorded envelopes from a real knot.

## Local Conventions

- Docstrings explain why, in prose; tests are named as sentences and assert rendered content.
- Value objects that mirror knot's records carry a per-class pylint disable with the reason in
  the docstring rather than a raised project limit.
- Findings deferred from a story are filed as tickets, never left as comments.
- A story's brainstorm, spec and plan live only as knot documents on its ticket (`other`, `spec`,
  `plan`, titled "<topic> brainstorm|design spec|implementation plan"), added with
  `knot document add` and updated with `knot document replace`. The harness drafts them under
  `docs/ai-assistant-ideation/`; attach them and delete the drafts before the story's commit, so no
  design document is committed outside `.tickets/docs/`.

## Gotchas

- knot's `check --json` answers `ok: false` together with `data.issues`; only `verdict` accepts
  that. Every other command goes through `answered`, which refuses any `ok: false`.
- Identifiers are passed after knot's `--` marker, so one starting with a dash is not an option.
- The digest asks knot for the tickets and documents directories once per `KnotCommand`; a panel
  pointed at a project whose `.knot.edn` moves either needs a restart. Documents are walked
  separately only when `:docs-dir` puts them outside the tickets directory.
- The reader's chosen tags live in the `knotview_tags` cookie; `/tags` (a GET) changes it and
  redirects back to a path on this panel only. Every list view narrows through `Tags.narrow`;
  the ticket page does not.
- The fidelity test skips without `knot` on PATH; the coverage gate still holds without it.
