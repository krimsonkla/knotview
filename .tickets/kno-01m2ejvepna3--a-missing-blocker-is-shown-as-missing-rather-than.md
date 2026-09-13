---
id: kno-01m2ejvepna3
title: A missing blocker is shown as missing rather than counted as open
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:50:14.997820Z'
updated: '2026-09-13T23:50:15.108213Z'
assignee: ''
---

## Description
knot reports a dependency on an id that does not exist as `{id, missing: true}` with no status. The envelope reader turns it into a Reference with a blank status, and Ticket.open_blockers counts it as open, so the tickets table shows one more open blocker than there is. Asserted as current behaviour in tests/values/test_ticket.py.

## Design
Carry `missing` on Reference, exclude missing references from open_blockers, and render them in the ticket page's blocked-by list with a chip that says missing, since a dangling dependency is exactly what the integrity section on the overview reports.
