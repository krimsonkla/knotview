---
id: kno-01m2ebf3c8mx
title: 'Test coverage: the reading and panel layers are untested against a 100 percent gate'
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T21:41:10.152601Z'
updated: '2026-09-13T21:41:10.269127Z'
assignee: ''
---

## Description
The test suite covers the console entry and the saved-projects file and nothing else. pytest is configured with fail-under=100 and reports 58 percent, so `pytest` exits non-zero on a clean checkout and the pre-commit gate cannot be trusted to mean anything.

Uncovered, as of the initial commit: the whole reading layer (knot_command 33 percent, knot_envelope 20 percent, backlog 62 percent), the panel (app 23 percent, selection 52 percent, tree 59 percent, overview 82 percent), and the value types' derived properties (ticket, project, unreadable_backlog).

## Design
Test the reading layer against recorded knot envelopes rather than a live knot, one fixture per command shape from the JSON protocol reference (ls-shape, single-ticket-shape with sections and inverse arrays, info, check with ok:false co-emitted). Test knot_command with a fake `knot` executable on PATH so the timeout, missing-binary and unparseable-stdout branches are each exercised. Test the panel through FastAPI's TestClient over a fake Backlog. Keep the read-only guard test that reads the source for write verbs.
