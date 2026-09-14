---
id: kno-01m2ebf4bfrd
title: 'Show knot''s graph metrics on the queues: leverage, coupling, level and component'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T21:41:11.150959Z'
updated: '2026-09-14T00:00:18.667167Z'
closed: '2026-09-14T00:00:18.667167Z'
assignee: Jason Risch
---

## Description
knot's listing rows carry four computed graph metrics, `leverage`, `coupling`, `level` and `cc`, and the envelope reader drops all four. knot's own guidance says leverage picks the next ticket when several are ready and level orders work into waves, which is exactly what a queue view is for.

## Design
Carry the four metrics on Ticket as nullable ints, since knot emits null for a singleton component or a closed row. Show leverage and level as columns on the ready and blocked queues and on the ticket table, sortable. Explain the columns in one line in the overview, quoting knot's definitions rather than inventing new ones.

## Notes

**2026-09-14T00:00:17.709765Z**

Task completed: Ticket carries knot's leverage, coupling, level and component from listing rows (None on a read, a closed row or a cycle); the ticket table shows lev and lvl columns, sortable, with a dash where knot gave no number; the queue pages say in one line what each means, in knot's own words. The recorder and fidelity test now describe recordings as (name, command, arguments) so multi-word commands can be recorded.
