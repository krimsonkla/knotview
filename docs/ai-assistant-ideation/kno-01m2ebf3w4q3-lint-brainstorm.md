# kno-01m2ebf3w4q3 — Lint brainstorm

Story: kno-01m2ebf3w4q3, "Lint: panel() complexity and the three value objects over the attribute
limit". Date: 2026-09-13. Mode: teams, quality-engineer challenger, two rounds.

## Problem

Four lint findings fail the pre-commit hooks on any commit touching their files: ruff C901 and
pylint R1260 on `panel()` in `src/knotview/panel/app.py` (McCabe 11 against 8); pylint R0902 on
`Ticket` (20 attributes against 7), `Project` (12) and `Selection` (9). Two items carried from
kno-01m2ebf3c8mx: the unknown-queue page reads "no a queue called X", and `Project.is_terminal`
has no caller.

## What the challenger measured

The 11 is not paths. `panel()` has one branch; each nested `def` costs one point and it holds nine
(the render helper, the exception handler, seven routes), so 1 + 9 + 1 = 11. Moving the handlers
into a module-level helper that loops over them measures 11 again: the complexity travels with the
closures. Only the class form, where each handler is a method, measures clean. A method-less
frozen dataclass raises no too-few-public-methods finding, checked on a synthetic file with the
project's pylint config.

## Approaches considered

1. **A `Pages` class in app.py** (chosen). Holds the backlog, the templates and the heartbeat;
   one method per page plus `rendered` and `unreadable`. `panel()` becomes assembly: build the
   app, mount static, register the exception handler, register each page with
   `app.add_api_route(path, method, methods=["GET"], response_class=...)`. The reason is design,
   not the number: today every handler closes over two locals, so which backlog a page reads is
   implicit in where the function was defined; on the class it is a named attribute, assembly is
   separate from rendering, and the route table is written out once as data.
2. A module-level `_routes()` helper. Rejected: relocates the finding without removing it.
3. Tune the McCabe limit for this file with a written reason. Rejected in favour of 1, which is
   a better structure on its own merits; the metric was counting closures, not paths.

For the value objects: per-class `# pylint: disable=too-many-instance-attributes` with the
reason in each docstring, no project-wide raise. Raising `max-attributes` to accommodate
`Ticket`'s 20 would silence the signal for every future class. The `min-public-methods`
precedent encodes a global style choice; an attribute count is a per-class fact.

## Decisions

- `Pages` class; `panel(backlog, *, heartbeat)` signature unchanged; no URL, template or
  response class changes; `_changes` and `_humanise` stay module-level.
- A route-surface test lands **before** the refactor, as its own commit: the exact path set
  including the `/static` mount, every `APIRoute`'s methods equal to `{"GET"}`, and the
  content-type of each HTML page and of `/digest`.
- The unknown-queue wording becomes "This panel has no queue called X" in the refactor commit,
  and `tests/panel/test_queue.py`'s pinned sentence is updated in the same commit, never
  weakened.
- `Ticket` and `Project`: disabled with the reason that the fields are knot's record shape and a
  nested split would hide the schema the reader mirrors. `Selection`: disabled with its own
  reason, that the fields are the query string the panel defines, one per filter the URL
  carries, and a split would move the filter list away from the one place `query_string` and
  `matches` read it.
- `Project.is_terminal` and its test are deleted; pylint is run on the file after the deletion
  and the result recorded before committing. Fallback if R0903 fires: a docstring-reasoned
  disable, never reinstated dead code.
- The ticket's "also makes the app testable per route" rationale is struck: every route is
  already tested per route at 100 percent coverage.
- Watch during implementation: `/static` is a `Mount`, so the methods assertion is scoped to
  `APIRoute`; confirm the methods set is exactly `GET` after the move rather than assuming it.
