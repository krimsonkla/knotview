---
id: kno-01m2ebf3w4q3
title: 'Lint: panel() complexity and the three value objects over the attribute limit'
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T21:41:10.660775Z'
updated: '2026-09-13T21:41:10.775576Z'
assignee: ''
---

## Description
Four lint findings fail the pre-commit hooks on the initial commit, which is why it was committed with --no-verify:

- ruff C901 and pylint R1260: `panel()` in src/knotview/panel/app.py has a McCabe complexity of 11 against a limit of 8.
- pylint R0902: `Ticket` in values/ticket.py has 20 instance attributes against a limit of 7.
- pylint R0902: `Project` in values/project.py has 12.
- pylint R0902: `Selection` in panel/selection.py has 9.

## Design
Split `panel()` so each route is its own named function or a small router module, which also makes the app testable per route. The three dataclasses are value objects whose fields are the record; either group related fields into nested values (graph references, timestamps, criteria) or, where a split would only hide the shape, record a per-class disable with a reason rather than lowering the project limit.
