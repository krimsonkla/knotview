# kno-01m2ebf3c8mx — Test coverage: the reading and panel layers, to the 100 percent gate

## Changes Since Last Cycle

- The ok:false carve-out in `verdict` now requires a **non-empty** `issues` list; an empty one is
  refused as a failed scan, with a test case (finding 13).
- The `broken` dispatch row is gone; which check envelope the fake prints is chosen by an
  environment variable the fixture sets (finding 14).
- `show` with the id `list` prints `list.json`, reaching the non-dict branch of `ticket` (15).
- The fake `info` rewrites the `paths` values to a per-test directory named by an environment
  variable, so `digest` tests run over a real directory (finding 16).
- AC 3 names the tests that discharge it; AC 7 is now a review-checklist item (12, 17).
- The ticket description is amended to say the story also fixes the integrity path (10).
- Noted that the devenv shell supplies `knot` through the tickets layer (11, declined).

Spec. Story kno-01m2ebf3c8mx. Brainstorm:
`docs/ai-assistant-ideation/kno-01m2ebf3c8mx-test-coverage-brainstorm.md`. Date: 2026-09-13.

## Problem

`pytest` runs with `--cov-fail-under=100` and branch coverage and reports 58 percent, so a clean
checkout fails and the gate carries no information. Only the console entry and the saved-projects
registry are tested. The reading layer, the panel and the value types' derived properties are not.

Probing knot 0.12.0 while designing the tests found that the integrity path cannot work: `knot
check --json` co-emits `ok: false` with `data.issues` whenever the project has an issue, and the
envelope reader refuses every `ok: false` envelope. So `KnotCommand.integrity` is dead code and the
overview page returns 503 on any backlog with one dangling reference, the opposite of what its
docstring promises.

## Goal

1. `pytest` exits zero on a clean checkout, at 100 percent line and branch coverage, with tests
   that assert behaviour rather than execute lines.
2. The integrity path works against a real knot: issues are shown on the overview, and a clean
   project shows none.
3. The suite does not depend on `knot` being on PATH for any covered line. The real binary is
   used only to check that the recorded fixtures are faithful.

## Out of scope

Refactors for the lint findings (kno-01m2ebf3w4q3), the 404 page for an unknown ticket, showing a
missing blocker as missing, and the unassigned tally filter. Each is recorded as a finding.

## Design

### Source changes, scoped

Only `src/knotview/reading/knot_command.py` and `src/knotview/reading/knot_envelope.py` change.

1. **A check-aware read.** `KnotCommand.integrity` no longer goes through `answered`. It reads
   the raw envelope and passes it to a new `knot_envelope.verdict(payload, *, attempting)` which:
   - refuses a non-dict payload and a `schema_version` other than 1, exactly as `answered` does;
   - returns `data` when `ok` is true;
   - returns `data` when `ok` is false **and** `data` is a dict whose `issues` is a **non-empty**
     list, which is knot's documented health-verdict carve-out (knot sets `ok: false` exactly
     when issues exist);
   - otherwise refuses with knot's own `error.message` where there is one, as `answered` does. An
     `ok: false` with no `issues` key, or with an empty `issues` list, is a failed scan, not a
     clean one, and renders the unreadable page.
   `_read` gains a keyword `verdict_read: bool = False` selecting which reader wraps the
   envelope, so the process handling stays in one place.
2. **Issue lines.** `_described` formats a dict issue as `<ids joined by space> <code>: <message>`
   plus ` (<path>)` when `path` is present, falling back to the whole issue as JSON when it
   carries none of those. String issues pass through unchanged.
3. **A docstring correction** on `_text`: knot omits an unset assignee from both the listing and
   the read, and writes a blank one as an empty string in both; the reader folds both to `None`.

### Fixtures

`tests/reading/envelopes/` holds envelopes recorded from a probe project on knot 0.12.0, already
captured: `info.json`, `list.json`, `closed.json`, `ready.json`, `blocked.json`,
`show-parent.json`, `show-child.json`, `check-clean.json`, `check-issues.json`, `not-found.json`.
Between them they hold: an absent assignee, a blank assignee, a named assignee, a parent and its
children (one archived), a blocker that is closed and one that is missing, a symmetric link, tags,
acceptance with one ticked, a section map with text before the first heading and a notes section,
graph metrics on list rows, a closed row with `closed`, a clean check, a check with one
`unknown_id` issue, and a `not_found` error.

A `tests/reading/envelopes/__init__.py` helper `envelope(name) -> dict` loads one.

### The fake knot

`tests/reading/conftest.py` writes one Python script into `tmp_path` and returns a `KnotCommand`
built with `knot=<script>` and `patience=0.5`. The script dispatches on its first argument, which
is always one of `READS` because `_spoken` puts the verb first:

| first argument | behaviour |
|---|---|
| `info` | print `info.json` with every value under `paths` rewritten to the directory named by `KNOTVIEW_FAKE_TICKETS` (the fixture sets it to `tmp_path / ".tickets"`, which it creates with an `archive/` subdirectory), so `digest` runs over a real directory |
| `list`, `closed`, `ready`, `blocked` | print the envelope of that name |
| `check` | print `check-issues.json` when `KNOTVIEW_FAKE_CHECK=issues`, `{"schema_version":1,"ok":false,"data":{"issues":[]}}` when `KNOTVIEW_FAKE_CHECK=empty`, `not-found.json` when `KNOTVIEW_FAKE_CHECK=error`, else `check-clean.json` |
| `show <id>` | `show-parent.json` or `show-child.json` by the recorded ids; `list.json` for the id `list` (a list where a ticket was expected); otherwise `not-found.json` with exit 1 |
| any verb, when `KNOTVIEW_FAKE_MODE=junk` | print `not json` and exit 0 |
| any verb, when `KNOTVIEW_FAKE_MODE=hang` | sleep 5 |

The fixture exposes a `fake(mode=..., check=...)` helper that sets those variables for one
`KnotCommand`, so each test names what it wants. The script never reads the real project. A
missing binary is exercised by constructing `KnotCommand(knot=str(tmp_path / "absent"))`.

### Tests: reading layer

`tests/reading/test_knot_envelope.py`, against the recorded envelopes:
- `answered` returns `data`; refuses a non-dict, a wrong `schema_version`, and `ok: false`
  carrying knot's message.
- `verdict` returns data for `check-clean.json` and `check-issues.json`; refuses `not-found.json`,
  an `ok: false` envelope whose data has no `issues` key, and an `ok: false` envelope whose
  `issues` is an empty list; refuses a wrong `schema_version` and a non-dict payload.
- `project_from`: every field from `info.json`; a null name reads as `unnamed`; a non-dict refuses.
- `tickets_from`: a list of rows; a non-list refuses; a non-dict row is skipped.
- `ticket_from`: absent, blank and named assignee; parent absent versus present; acceptance;
  tags; a missing id refuses; from `show-child.json` the blockers include the missing one with a
  blank status; from `show-parent.json` the sections keep order and the blank heading holds the
  preamble, empty sections are dropped, children include the archived child.

`tests/reading/test_knot_command.py`, through the fake:
- `project`, `live`, `closed`, `ready`, `blocked`, `ticket` each return values from their
  envelope; `ticket` on an unknown id refuses with knot's message.
- `ticket` when show answers a list refuses with the "rather than a ticket" advice.
- `integrity` returns `()` on a clean check and the formatted lines on `check=issues`; the line
  carries the id, the code and the message; `check=empty` and `check=error` both refuse. The
  line formatter is also tested directly: a string issue passes through, `path` is appended
  when present, a dict without the known keys renders as JSON.
- `mode=junk` refuses naming the command; `mode=hang` refuses naming the patience; a missing
  binary refuses naming the path.
- `_read` with a verb outside `READS` refuses, called directly with a comment explaining that no
  public method can reach it by design.
- `digest` is `absent` when the tickets path is not a directory; stable across two calls; moves
  when a file's mtime moves; covers the archive.
- The read-only guard, structural rather than lexical: exactly one module under `knotview/`
  mentions a process-spawning token (`subprocess`, `os.system`, `os.popen`, `os.exec`,
  `os.spawn`, `pty.`), and it is `reading/knot_command.py`; `READS` is disjoint from knot's
  write verbs; and `_spoken` is asserted to put the given verb first and `--json` last. A
  word-scan was rejected at plan review because `"status"` is also a field name.

`tests/reading/test_real_knot.py`, marked `slow`, skipped without `knot` on PATH. The devenv
shell provisions `knot` 0.12.0 through the tickets layer selected in `devenv.config.toml`, and
the `knot-check` pre-commit hook already depends on it, so in this project's own environment the
test runs; the skip exists for a bare `pip install` checkout.
- `knot init` in `tmp_path`, then the same ticket files the probe used, written directly.
- The real `KnotCommand` produces a project, live, closed, ready, blocked, one ticket and the
  integrity lines whose **shapes** match the fixtures: the same key sets on each raw envelope's
  data, the same ids, statuses, assignees, section headings, blocker ids and issue codes.
  Timestamps and paths are not compared. This test may not be the only cover for any source
  line; the coverage run without it must still be 100.

`tests/reading/test_snapshot.py`: `Snapshot.read` calls each port once and carries the results.

### Tests: panel

`tests/panel/declared.py`: `DeclaredBacklog`, a frozen dataclass implementing `Backlog` over
tuples, with a `refusing` variant whose every method raises `UnreadableBacklog`, and a `digests`
sequence for the stream test. It records how many times `digest` was called.

Each page test uses `TestClient(panel(backlog))` synchronously and asserts rendered text:
- `test_overview.py`: tally counts and their filter links for every declared type, status and
  priority including zero counts; queue counts; the unassigned count; live total; parents listed
  by priority; recently closed capped at 8; the integrity section absent when clean and listing
  each line when not.
- `test_tickets.py`: each filter narrows (type, status, priority, mode, assignee, tag, query on
  id, title and tag); an undeclared value is dropped; `closed=1` includes the archive; each order
  including descending `updated` and `created`; ties break on id; the summary line reads
  `N of M`; the clear link appears only when filtering; `query_string` round-trips and omits the
  default order.
- `test_tree.py`: branches by parent priority, children by priority, `done/total` and
  `met/criteria` rendered, the complete-but-open notice, orphans listed, a child whose parent is
  not live is an orphan.
- `test_queue.py`: `ready` and `blocked` render their tickets; an unknown queue renders the
  "nothing here" page at 200.
- `test_ticket.py`: title, chips, humanised timestamps, the dash for a missing timestamp,
  acceptance with met count, narrative sections in order with the blank-heading preamble, each
  graph direction, external refs, notes; an unknown id renders the unreadable page at 503.
- `test_unreadable.py`: the refusing backlog renders message and advice at 503 on `/`.
- `test_live.py`: `/digest` returns the digest; `/live` with heartbeat 0 over digests
  `A, A, B, raise` yields `event: changed` A, the keepalive comment, `event: changed` B,
  `event: unreadable`, and the iterator is exhausted inside the stream context. One test pins
  the digest call count per event as a baseline.
- `_humanise`: `2026-09-13T21:45:04.037646Z` renders `2026-09-13 21:45`; `None` renders the dash.

### Tests: values

`tests/values/test_ticket.py`: `met`, `criteria`, `unmet`, `open_blockers` (a blank-status
missing blocker counts as open, asserted as current behaviour), `notes`, `narrative`.
`tests/values/test_project.py`: `open_statuses`, `priorities`, `is_terminal`.
`tests/values/test_unreadable_backlog.py`: the message joins message and advice.

## Acceptance criteria

1. `pytest` on a clean checkout exits zero at 100 percent line and branch coverage.
2. `pytest -m "not slow"` also reports 100 percent, proving the real-knot test covers nothing
   exclusively.
3. The overview page renders an integrity line naming the ticket id and the code `unknown_id`,
   at 200. Discharged by `tests/panel/test_overview.py` over a declared backlog whose integrity
   lines come from `check-issues.json` through the real formatter, and by
   `tests/reading/test_knot_command.py` with `check=issues`; the real-knot fidelity test
   confirms the same issue code arrives from the binary.
4. Against a clean check the overview renders no integrity section.
5. A failed scan (`ok: false` with no `issues` key, or an empty list) renders the unreadable
   page, asserted in `test_knot_envelope.py` and `test_knot_command.py`.
6. Only `reading/knot_command.py` can start a process, `READS` holds no write verb, and
   `_spoken` speaks only the verb it is given, each asserted by a test.
7. No `# pragma: no cover` is added: `grep -rn "pragma: no cover" src tests` is empty.

Review checklist, verified by reading rather than by a command: every page test asserts rendered
content, not only a status code.

## Testing strategy

Unit tests over recorded envelopes for the reader; a fake executable for the process boundary;
`TestClient` over a declared backlog for the pages; one slow fidelity test over the real binary.
Verified by `pytest` and `pytest -m "not slow"` both at 100.

## Cross-story collision check

No `_references/project/` high-risk-surfaces doc is present in the harness, and the repo has no
open pull requests, so no collision scan applies. No collision found.
