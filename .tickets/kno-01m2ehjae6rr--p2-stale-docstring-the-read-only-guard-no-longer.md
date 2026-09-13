---
id: kno-01m2ehjae6rr
title: '[P2] Stale docstring: the read-only guard no longer reads the source for write verbs'
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:47.142681Z'
updated: '2026-09-13T23:27:47.268119Z'
assignee: ''
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the hygiene lens and confirmed by an adversarial verifier.

### From the hygiene lens: Stale comment: the read-only guard no longer 'reads the source' for write verbs

Evidence: src/knotview/reading/knot_command.py:29-31 says "knot's write verbs are create, start, ... and none of them appears here or anywhere else in this package. A guard reads the source and says so." The actual guard, tests/reading/test_knot_command.py:166-181, asserts `set(READS).isdisjoint(WRITE_VERBS)` and that only reading/knot_command.py imports subprocess; its docstring (lines 171-173) explicitly says the guard is NOT on which words appear in the package, because "status" is also a field name. Likewise src/knotview/reading/backlog.py:19 says "the backlog stays AI-driven" while README.md:26 says "driven by whatever drives it". app.py's docstrings were checked against the Pages/ROUTES refactor and are accurate.

Recommendation: Reword knot_command.py:29-31 to match the structural guard (READS is disjoint from the write verbs; only this module may spawn a process) and align backlog.py:19 with the README wording.

Verifier (P2, blocks public: no): Reproduced at fcc6b66. src/knotview/reading/knot_command.py:29-31 claims the write verbs appear nowhere "here or anywhere else in this package" and that "a guard reads the source and says so"; the actual guards in tests/reading/test_knot_command.py:166-181 assert set(READS).isdisjoint(WRITE_VERBS) and that reading/knot_command.py is the only module containing a process-spawning token, and the test docstring (171-173) explicitly says the guard is NOT on which words appear because "status" is also a field name. A grep confirms "status" occurs in ten modules of the package (ticket.py, project.py, tree.py, overview.py, app.py, etc.), so the comment's "none of them appears anywhere else in this package" is literally false as well as stale; the class docstring at line 44 ("Nothing in this package holds a write verb") has the same defect. The secondary point also reproduces: backlog.py:19 says "the backlog stays AI-driven" while README.md:26 (and the egg-info copy) says "driven by whatever drives it". Both are comment/docstring wording only; the enforced guarantee is correct and tested, so this is polish, not a blocker.
