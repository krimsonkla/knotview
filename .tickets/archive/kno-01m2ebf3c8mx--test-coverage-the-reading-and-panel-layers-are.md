---
id: kno-01m2ebf3c8mx
title: Test coverage to the 100 percent gate, and the integrity path knot's check actually reaches
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T21:41:10.152601Z'
updated: '2026-09-13T22:46:32.192707Z'
closed: '2026-09-13T22:46:32.192707Z'
assignee: Jason Risch
---

## Description
The test suite covers the console entry and the saved-projects file and nothing else. pytest is configured with fail-under=100 and reports 58 percent, so `pytest` exits non-zero on a clean checkout and the pre-commit gate cannot be trusted to mean anything.

Uncovered, as of the initial commit: the whole reading layer (knot_command 33 percent, knot_envelope 20 percent, backlog 62 percent), the panel (app 23 percent, selection 52 percent, tree 59 percent, overview 82 percent), and the value types' derived properties (ticket, project, unreadable_backlog).

This story also fixes one defect found while designing the tests, because a fixture recorded from the current behaviour would freeze it as the contract: `knot check --json` answers `ok: false` alongside its issues, and the envelope reader refuses every `ok: false` envelope, so the integrity path is dead code and the overview page returns 503 on any backlog with a dangling reference. The fix is a check-aware read in knot_command and knot_envelope, plus the issue formatter reading `ids` (plural) as knot writes it. Nothing else under src changes.

## Design
Test the reading layer against envelopes recorded from knot 0.12.0 rather than transcribed from the protocol reference. Test knot_command with a fake `knot` script injected through the constructor, so the timeout, missing-binary, unparseable-stdout and refusal branches are each exercised. Test the panel through FastAPI's TestClient over a declared Backlog, asserting rendered content. Keep the read-only guard test that reads the source for write verbs. One slow test drives the real knot for fidelity only and covers no line exclusively. Spec: docs/ai-assistant-ideation/kno-01m2ebf3c8mx-test-coverage-spec.md.

## Notes

**2026-09-13T21:45:04.037646Z**

Starting work on this task.

**2026-09-13T22:45:59.928493Z**

Implementation artifacts attached
branch: jr/kno-01m2ebf3c8mx-test-coverage commit: 4f443a35766e73610ff82662d837cd9b6cc2799a
- Brainstorm: docs/ai-assistant-ideation/kno-01m2ebf3c8mx-test-coverage-brainstorm.md @ 4f443a35766e73610ff82662d837cd9b6cc2799a
- Spec: docs/ai-assistant-ideation/kno-01m2ebf3c8mx-test-coverage-spec.md @ 4f443a35766e73610ff82662d837cd9b6cc2799a
- Plan: docs/ai-assistant-ideation/kno-01m2ebf3c8mx-test-coverage-plan.md @ 4f443a35766e73610ff82662d837cd9b6cc2799a

**2026-09-13T22:46:31.638529Z**

Task completed: the reading and panel layers are tested to the 100 percent gate (138 tests, 100 percent line and branch; 128 without the slow real-knot test, also 100), and the integrity path now works: knot check's ok:false health verdict is read as data, issues render on the overview instead of a 503, and the issue formatter reads ids, code, message and path as knot writes them. Envelopes recorded from knot 0.12.0 back the reader tests; a fake knot injected through the constructor drives every failure branch; a slow fidelity test keeps the recordings honest against the binary. Branch jr/kno-01m2ebf3c8mx-test-coverage, commits cfab810..4f443a3. Deferred with reasons: the unknown-queue grammar and Project.is_terminal to kno-01m2ebf3w4q3; a missing blocker shown as missing, a 404 for an unknown ticket, the tree dropping a child of a non-live parent, and the unassigned tally filter each need a follow-up ticket.
