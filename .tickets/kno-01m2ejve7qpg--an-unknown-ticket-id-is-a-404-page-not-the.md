---
id: kno-01m2ejve7qpg
title: An unknown ticket id is a 404 page, not the unreadable page at 503
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:50:14.519180Z'
updated: '2026-09-13T23:50:14.627437Z'
assignee: ''
---

## Description
knot answers `not_found` for an id it cannot resolve, and the panel surfaces that through the UnreadableBacklog handler as the unreadable page at 503, which is the wrong story: the backlog was read fine, the ticket is not there. Asserted as current behaviour in tests/panel/test_ticket.py.

## Design
Have KnotCommand.ticket raise a distinct refusal for knot's `not_found` code (the envelope carries it), and give the panel a 404 page for it that offers the ticket list, keeping 503 for a backlog that cannot be read at all.
