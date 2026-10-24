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
- `src/knotview/reading/` the `Backlog` port, its one implementation over `knot ... --json`, the
  envelope reader, and `GitWorktrees`, which lists the repository's worktrees
- `src/knotview/panel/` the FastAPI app (`Pages` and `panel()`), the selection, tree, overview,
  trend, comparison and related-ticket values, the worktree resolver and cookie, the templates
  and the static files
- `src/knotview/values/` frozen dataclasses: Ticket, Project, Criterion, Reference, Worktree, and
  the two refusals
- `scripts/` maintenance tools outside the package and the coverage gate: `vendor_primer.py`
  rebuilds the Primer tokens, `capture_screenshots.py` (with `capture_check.py`) rebuilds the
  README's tour from a demo backlog
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
method per page. The look is a vendored subset of Primer Primitives (`static/primer.css`) under
knotview's own `kv-` components in `panel.css`, light or dark by the system unless the reader
chose a theme (a `data-theme` attribute set from localStorage before the page draws). `Selection`
is the only URL builder: `/tickets` redirects any other spelling of a query to
`Selection.query_string`'s, and the filter form's script serialises the form without building a
URL of its own. Every route is a GET, `READS` is disjoint from knot's write verbs, and only
`reading/knot_command.py` and `reading/git_worktrees.py` may start a process; tests assert all
three. git is only ever asked `worktree list --porcelain -z`. Each open page carries the digest it
was rendered under and asks `/digest` about once a second (not while hidden) for a digest of the
ticket and document files' names and modification times, reloading itself when the answer differs
from what it carries. It polls rather than holding a stream, because a browser allows six
connections to one host and a stream per tab exhausted them. Page handlers, the refusal pages'
included, are plain functions, so their knot reads run in the thread pool; the backlog is
therefore read from several threads at once, and anything a reader caches must be safe to compute
concurrently (`KnotCommand` locks its one cached value). A hidden tab does not poll and asks as
soon as it is shown. Only a page that carries no digest asks once while hidden, to learn what it
was rendered from. A panel that stops answering is asked less often, up to twice a minute.

A repository's worktrees each hold their own `.tickets/`. `GitWorktrees` lists them; the
`Backlogs` resolver in `panel/worktrees.py` keeps one `KnotCommand` per worktree under a lock and
picks one per request from the `knotview_worktree_<digest>` cookie, matched against git's list
(anything unlisted reads the launch directory). `Pages._backlog(request)` settles the listing, the
choice and the page's carried digest once per request; `/digest` checks the cookie against the last
page render's listing and never runs git.

`/compare?with=<path>` compares the chosen worktree's backlog with one other listed worktree.
`Backlogs.beside` matches `with` against git's list (never the worktree being read) and returns the
same cached `KnotCommand` a choice of that worktree uses; anything unlisted reads nothing and shows
the picker. `panel/comparison.py` sorts tickets into only-here, only-there, closed on one side,
changed (status, priority, title, type) and alike. The page carries both digests joined with `~`
and names `/digest?with=<path>` in `data-follow` on `#live`, so `follow.js` polls that instead and
reloads when either side moves; an unreadable other side is carried as `-`.

## Key Files

- `src/knotview/reading/knot_command.py`: `READS`, `_spoken` (argv with `--json --`), the
  check-aware `integrity`, and the digest.
- `src/knotview/reading/knot_envelope.py`: `answered` and `verdict` (knot's `check` co-emits
  `ok: false` with data), `ticket_from`, `project_from`.
- `src/knotview/panel/app.py`: `Pages`, `ROUTES`, `panel()`, `HOSTS`.
- `src/knotview/panel/static/follow.js`: the digest poll, the since-last-looked marks, local time,
  filters that apply on change, the More filters dialog, pinning a tag, and the theme switch.
- `src/knotview/panel/static/fold.js`: remembered folds (`details[data-fold]`), ticket tabs, the
  overview's chart choices and opening a dialog from a button.
- `src/knotview/panel/static/primer.css`: generated Primer tokens; `panel.css`: the `kv-` components.
- `src/knotview/panel/templates/_row.html`, `_rows.html`, `_filters.html`: one ticket row shared by
  every list and the tree (a tree branch passes `row_tag="summary"` and its counts as `fact`), and
  the tickets page's filters.
- `src/knotview/panel/selection.py`: every filter the URL carries, and the query-string builder.
- `src/knotview/panel/tags.py`: the sticky tag choice, its cookie, and `narrow`.
- `src/knotview/reading/git_worktrees.py`: `GitWorktrees`, the pinned git argv, the porcelain
  parser.
- `src/knotview/panel/worktrees.py`: `Backlogs`, the per-worktree reader cache and the choice.
- `src/knotview/panel/worktree_choice.py`: the worktree cookie's name, encoding and matching.
- `src/knotview/panel/comparison.py`: `Comparison`, two worktrees' tickets grouped by difference.
- `src/knotview/panel/related.py`: `Related`, the ticket page's lookup of each related id in the
  live, closed and ready listings, with the fact each tab adds.
- `tests/reading/conftest.py`: the fake `knot` and `git` scripts the reading tests drive.
- `tests/reading/record_envelopes.py`: regenerates the recorded envelopes from a real knot.

## Local Conventions

- Docstrings explain why, in prose; tests are named as sentences and assert rendered content.
- Value objects that mirror knot's records carry a per-class pylint disable with the reason in
  the docstring rather than a raised project limit.
- Findings deferred from a story are filed as tickets, never left as comments.
- A page is built at the density its approved mockup shows. Anything more is hidden by default
  behind a per-reader choice kept in the browser, as the overview's charts are.
- Labels come from the project's `.knot.edn` and its data, never from a word picked here: the
  overview names its parents by the types they have, and says "parents" only as a fallback.
- Colour follows the same rule. A status pill (`_status.html`) is coloured by
  `Project.status_role` (intake, active, stage, closing, terminal), never by the status word, so
  `panel.css` has one rule per role. The overview's status dots and bars use the same roles
  (`kv-dot r-<role>`, `kv-fill r-<role>`); no rule is keyed on a status word.
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
- The worktree cookie is named per launch directory (`knotview_worktree_` plus a digest), because
  browsers share cookies across ports. Its value is a percent-encoded path, only used once it
  matches git's current list.
- A page reads its digest before its data and carries it as `data-digest` on `#live`; `follow.js`
  starts from it. A refused digest read renders the page without one. The launch directory's
  digest is the bare backlog digest; other worktrees' are prefixed with a digest of their path.
- Worktrees need git 2.36 or later (`-z`); an older or missing git silently means one worktree.
- `primer.css` is generated: refresh it only with `scripts/vendor_primer.py`, which checks each
  file's pinned sha256. Semgrep in the hooks rejects network calls in the repository, so the
  script reads files you fetch with `curl` (the command is in its docstring).
- Fold memory is per tab (sessionStorage) on the ticket page and the More filters dialog, and
  across visits (localStorage) on the tree and the overview's charts.
- The worktree and pinned-tag cookies ignore the port, so a second panel on the same machine
  over the same directory shares them; a panel left on another worktree moves the others too.
- The overview's charts over time (`panel/trend.py`) come only from each ticket's `created` and
  `closed` instants. There is no history store, so a past status, priority or type cannot be
  charted; do not add one that writes, since the panel never writes.
- The README's one image, `docs/screenshots/tour.webp`, is rebuilt with
  `uv run python -m scripts.capture_screenshots`; it needs Chrome (`KNOTVIEW_CHROME` overrides the
  path) and Pillow from the dev group. Keep it the only image, so the README has one picture to
  refresh and nothing per view to fall out of date.
