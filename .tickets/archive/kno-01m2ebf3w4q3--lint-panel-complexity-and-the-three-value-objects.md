---
id: kno-01m2ebf3w4q3
title: 'Lint: panel() complexity and the three value objects over the attribute limit'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T21:41:10.660775Z'
updated: '2026-09-13T23:11:51.995251Z'
closed: '2026-09-13T23:11:51.995251Z'
assignee: Jason Risch
---

## Description
Four lint findings fail the pre-commit hooks on the initial commit, which is why it was committed with --no-verify:

- ruff C901 and pylint R1260: `panel()` in src/knotview/panel/app.py has a McCabe complexity of 11 against a limit of 8.
- pylint R0902: `Ticket` in values/ticket.py has 20 instance attributes against a limit of 7.
- pylint R0902: `Project` in values/project.py has 12.
- pylint R0902: `Selection` in panel/selection.py has 9.

## Design
Move the route handlers onto a `Pages` class, one method per page, so `panel()` is assembly only: the McCabe count was counting nine closures, not paths, and on a class each page's backlog is a named attribute rather than an implicit closure binding. Every route is already tested per route at 100 percent coverage, so testability is not the reason. The three dataclasses are value objects whose fields are the record; either group related fields into nested values (graph references, timestamps, criteria) or, where a split would only hide the shape, record a per-class disable with a reason rather than raising the project limit. Also here: the unknown-queue page's "no a queue" wording, and deleting the uncalled `Project.is_terminal`.

## Notes

**2026-09-13T22:51:23.515311Z**

Starting work on this task.

**2026-09-13T23:11:29.878520Z**

Implementation artifacts attached
branch: jr/kno-01m2ebf3w4q3-lint commit: 8b9e725bab8194191430e9e64aebe92ea49d4cd4
- Brainstorm: docs/ai-assistant-ideation/kno-01m2ebf3w4q3-lint-brainstorm.md @ 8b9e725bab8194191430e9e64aebe92ea49d4cd4
- Spec: docs/ai-assistant-ideation/kno-01m2ebf3w4q3-lint-spec.md @ 8b9e725bab8194191430e9e64aebe92ea49d4cd4
- Plan: docs/ai-assistant-ideation/kno-01m2ebf3w4q3-lint-plan.md @ 8b9e725bab8194191430e9e64aebe92ea49d4cd4

**2026-09-13T23:11:51.411165Z**

Task completed: ruff and pylint are clean over src and tests, so every file commits through the hooks. panel() is assembly over a Pages class with one method per page and a ROUTES table; the McCabe 11 was counting nine closures, not paths, and the reason for the class is design: a page's backlog is a named attribute and assembly is separate from rendering. Ticket, Project and Selection carry per-class too-many-instance-attributes disables with per-class reasons; pyproject is untouched. Project.is_terminal, which had no caller, is deleted. The unknown-queue page now reads "This panel has no queue called X". A route-surface test pinning the exact path set, GET-only methods and content-types landed before the refactor. 145 tests at 100 percent line and branch. Branch jr/kno-01m2ebf3w4q3-lint, commits 0094576..8b9e725.
