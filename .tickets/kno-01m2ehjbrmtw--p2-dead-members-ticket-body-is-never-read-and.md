---
id: kno-01m2ehjbrmtw
title: '[P2] Dead members: Ticket.body is never read and SavedProjects.names has no caller outside tests'
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:48.500037Z'
updated: '2026-09-13T23:27:48.629553Z'
assignee: ''
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the hygiene lens and confirmed by an adversarial verifier.

### From the hygiene lens: Dead members: Ticket.body is populated but never read; SavedProjects.names() has no caller outside tests

Evidence: src/knotview/values/ticket.py:46 `body: str | None = None` is set by src/knotview/reading/knot_envelope.py:139 `body=_text(stated, "body")`; grep for `\.body\b` and `ticket.body` across src, templates and tests returns 0 hits, so no page and no assertion uses it. src/knotview/entry/saved_projects.py:33 `names()` is called only from tests/entry/test_saved_projects.py:51,59; console.py never lists saved names.

Recommendation: Drop `body` from Ticket and ticket_from (sections already carry the text), or render it; either expose `names()` through a `--list` flag in console.py or delete it.

Verifier (P2, blocks public: no): Reproduced both halves. `Ticket.body: str | None = None` is at src/knotview/values/ticket.py:46 and is populated by `body=_text(stated, "body")` at src/knotview/reading/knot_envelope.py:139; a grep for `\.body\b`, `ticket.body` and `body=` across src/ (py, html, jinja) and tests/ finds no other reader or assertion, only prose comments containing "nobody"/"somebody", so the field is written and never consumed, while `sections` (with the "" preamble key) is what the tests and pages use for the ticket text. `SavedProjects.names()` at src/knotview/entry/saved_projects.py:33 is called only from tests/entry/test_saved_projects.py:51 and :59; console.py's argparse defines `project`, `--repository`, `--port`, `--save`, `--knot` and no listing flag, and `named()` builds its own "saved: ..." advice from `_read()` rather than through `names()`. Nothing here is user-visible, mis-behaving or a contributor stumbling block; it is unused surface in a small value record and a one-line convenience method, so P2 polish and not a public blocker.
