---
id: kno-01m2ejvepna3
title: A missing blocker is shown as missing rather than counted as open
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:50:14.997820Z'
updated: '2026-09-13T23:54:11.485407Z'
closed: '2026-09-13T23:54:11.485407Z'
assignee: Jason Risch
---

## Description
knot reports a dependency on an id that does not exist as `{id, missing: true}` with no status. The envelope reader turns it into a Reference with a blank status, and Ticket.open_blockers counts it as open, so the tickets table shows one more open blocker than there is. Asserted as current behaviour in tests/values/test_ticket.py.

## Design
Carry `missing` on Reference, exclude missing references from open_blockers, and render them in the ticket page's blocked-by list with a chip that says missing, since a dangling dependency is exactly what the integrity section on the overview reports.

## Notes

**2026-09-13T23:54:10.911886Z**

Task completed: Reference carries knot's missing flag; open_blockers leaves a missing blocker out, so the tickets table no longer counts it; the ticket page shows it as a missing chip with its id and no link. Asserted in the envelope, values and page tests.
