# kno-01m2ebf3c8mx — Test coverage brainstorm

Story: kno-01m2ebf3c8mx, "Test coverage: the reading and panel layers are untested against a
100 percent gate". Date: 2026-09-13. Mode: solo with a quality-engineer challenger, two rounds.

## Problem

pytest runs with `--cov-fail-under=100` and branch coverage and reports 58 percent. The console
entry and the saved-projects registry are fully tested; the reading layer, the panel and the value
types' derived properties are not. A clean checkout fails `pytest`, so the gate means nothing.

## Prior art

- `tests/entry/test_console.py`, `tests/entry/test_saved_projects.py`: tmp_path helpers, no
  mocks, sentence-style names, a module docstring stating the unit.
- The `slow` marker in pyproject: "drives a real knot project on disk; kept in the default run".
- The Backlog protocol docstring: the one real implementation "is exercised against a real
  project so the contract is known to hold".
- `panel(backlog)` takes any Backlog, so pages are testable with FastAPI's TestClient and no
  process.

## What the challenger found against knot 0.12.0

Three facts in the first design were false, probed on a throwaway project:

1. `knot check --json` co-emits `ok: false` with `data` whenever issues exist, and
   `answered()` refuses every `ok: false` envelope. So `KnotCommand.integrity` can only return
   an empty tuple or raise, the `_described` helper is dead code, and the overview page returns
   503 for any backlog with one dangling reference. The source docstring promises the opposite.
2. An unset assignee is absent from both the listing and the read shape; a blank one is an
   empty string in both. The `_text` docstring's listing-versus-read rationale is wrong.
3. Integrity issues carry `ids` (plural), `code`, `severity`, `message`, and sometimes `path`.
   `_described` looks for `id` singular, so it drops the ticket ids.

Also observed: a missing blocker arrives as `{id, missing: true}` with no status, which the
reader turns into a Reference with a blank status that `open_blockers` counts as open; list rows
carry `cc`, `coupling`, `level`, `leverage`; `info` returns a null project name on a fresh
`init`; the archive sits inside the tickets path so `digest` already covers it.

## Approaches considered

1. **Fake `knot` executable, injected through the constructor** (chosen). `KnotCommand` already
   takes `knot=` and `patience=`, so one argv-dispatching script reaches every success and
   failure branch with no PATH work and no leakage between tests.
2. Monkeypatch `subprocess.run`. Rejected: the timeout and missing-binary branches become
   assertions about the mock rather than about behaviour.
3. Only a real knot. Rejected: cannot reach the failure branches, and would make the coverage
   gate depend on the binary being present.

## Decisions

- **Scoped source fix in this story.** The check envelope is read through a check-aware path
  that accepts `ok: false` when `data.issues` is present, still enforces `schema_version`, and
  still refuses an `ok: false` envelope with no `issues` key. `_described` formats from `ids`,
  `code`, `message`, and `path` when present. The `_text` docstring is corrected. Nothing else
  in `src/` changes. Reason: a fixture recorded from the current behaviour would freeze a
  defect as the contract, and the fix is a few lines.
- **Fixtures are recorded, not written.** Real envelopes from a probe project live under
  `tests/reading/envelopes/`. They include absent and blank assignees, a missing blocker, list
  rows with graph metrics, a closed row, a section map with a blank-heading preamble, a clean
  check, a check with issues, and a not-found error.
- **The real-knot test is fidelity only.** Marked `slow`, skipped when `knot` is not on PATH,
  it writes ticket files directly into a `knot init`'d tmp project (the repo's ticket-discipline
  hook blocks knot write verbs), runs the real command, and compares the shapes of what it gets
  against the recorded fixtures. It covers no source line exclusively; the fake path covers all
  of them.
- **The refusal branch** in `_read` is tested by calling `_read` directly with a comment saying
  why: no public method can reach it by design. No pragma.
- **The live stream** is consumed with `client.stream` over a backlog whose digest answers A, A,
  B and then raises, so the test asserts the changed event, the keepalive comment, the second
  changed event and the unreadable event, and asserts inside the stream context that the
  iterator is exhausted.
- **Status codes, stated.** An unknown queue name renders `unknown.html` at 200. An unknown
  ticket id currently surfaces knot's not_found through the 503 handler; asserted as current
  behaviour and recorded as a P2 finding for a follow-up 404 page.
- **Every page test asserts rendered content**, because coverage counts Python only: tally
  counts and links, the humanised timestamp and its dash fallback, branch progress, the
  preamble text under the blank heading, the integrity lines, the unreadable page's advice.
- All TestClient tests are synchronous (asyncio auto mode plus a sync client deadlocks).
- The digest call count per heartbeat is pinned in one test as a baseline for a later story.

## Findings to carry forward (not this story)

- `Project.is_terminal` has no caller in the package or templates. Tested anyway; filed for
  kno-01m2ebf3w4q3.
- The unassigned tally carries an assignee filter with an empty value that no URL can express,
  since `Selection.asked` maps a blank assignee to ANY. Filed as a finding.
- A missing blocker should probably be shown as missing rather than counted as open. Filed.
- An unknown ticket id should be a 404 page rather than a 503. Filed.

## Layout

```
tests/reading/envelopes/*.json      recorded from knot 0.12.0
tests/reading/test_knot_envelope.py
tests/reading/test_knot_command.py  argv-dispatching fake, digest, refusal, read-only guard
tests/reading/test_real_knot.py     slow, fidelity only
tests/reading/test_snapshot.py
tests/panel/declared.py             DeclaredBacklog over tuples
tests/panel/test_overview.py  test_tickets.py  test_tree.py  test_queue.py
tests/panel/test_ticket.py    test_live.py     test_unreadable.py
tests/values/test_ticket.py   test_project.py  test_unreadable_backlog.py
```
