---
id: kno-01m3ratb96qf
title: A ticket with no id makes every page answer 503
status: closed
type: task
priority: 2
mode: afk
created: '2026-09-30T04:57:56.261031Z'
updated: '2026-09-30T05:01:00.270856Z'
closed: '2026-09-30T05:01:00.270856Z'
assignee: Jason Risch
---

A live ticket file with no `id` in its frontmatter makes every page answer 503. knot 0.15 lists that ticket as a row without an `id`, and every read verb answers `ok: true`. But the panel's `tickets_from` refuses the whole listing on that one row ("a ticket was stated with no id"), so `live`, `ready` and `blocked` fail, and the overview, the lists and every ticket page with them. knot's own check reports the file as `missing_required_field`, which is exactly what the integrity card exists to show, and it cannot show it while the page is a 503. Found by /code-review high on kno-01m3qr3peyx7.

## Design

In a listing, skip a row with no id instead of refusing the listing, so the rest of the backlog renders and the integrity card reports the broken file. A single ticket read (`show`) still refuses a record with no id, since there the one thing asked for cannot be read.

## Notes

**2026-09-30T04:58:06.327434Z**

Starting work on this task.

**2026-09-30T05:00:59.603029Z**

Fixed in 9f70d3b. Every listing goes through tickets_from, including live, closed, ready, blocked and the primer's three lists. It now leaves out a row with no id instead of refusing the whole listing. A single ticket read still refuses a record with no id.

Verified against knot 0.15.0 with a real server over a project holding a ticket file with no id:
- /, /tickets, /tree, /queue/ready and a ticket page all answer 200;
- the integrity card shows "missing_required_field: missing required field :id".

Tests at the envelope level and against the real binary. /code-review high found no bugs; its one note, a test assertion that could never fail, is tightened.
