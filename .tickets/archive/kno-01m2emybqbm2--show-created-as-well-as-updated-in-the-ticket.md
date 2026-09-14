---
id: kno-01m2emybqbm2
title: Show created as well as updated in the ticket table
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:47.403550Z'
updated: '2026-09-14T00:50:39.311653Z'
closed: '2026-09-14T00:50:39.311653Z'
assignee: Jason Risch
---

## Description
The ticket table shows the updated instant only, while the tickets page already orders by created. A reader ordering by created sees the order but not the values.

## Design
Show the instant the current order is by: updated by default, created when ordered by created, with the column heading naming which. Keep one instant column so the table stays narrow.

## Notes

**2026-09-14T00:50:38.614078Z**

Task completed: the table's one instant column shows created when the order is by created and updated otherwise, its heading offering both orders with the active one underlined, so the table stays narrow and the value matches the sort.
