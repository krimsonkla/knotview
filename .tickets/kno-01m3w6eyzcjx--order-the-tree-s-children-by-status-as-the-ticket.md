---
id: kno-01m3w6eyzcjx
title: Order the tree's children by status, as the ticket page does
status: open
type: task
priority: 2
mode: afk
created: '2026-10-01T16:58:46.635243Z'
updated: '2026-10-01T16:58:46.802798Z'
assignee: ''
---

The ticket page orders a ticket's children and its siblings by the project's declared status order (kno-01m3w61pvk11), but the tree page still lists each node's children in knot's order. A reader moving between the two sees one epic's children in two orders.

## Design

Order the tree's children the same way, through `Project.by_status` or an equivalent over the tree's own nodes. The tree builds its children from `Tree`, not from `Reference`, so this is a separate change. Decide whether a node's whole subtree moves with it, which it should, since the order is among siblings.