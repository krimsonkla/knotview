---
id: kno-01m2emy8t442
title: Show connected components on the tree page
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:44.420420Z'
updated: '2026-09-14T00:41:13.246003Z'
closed: '2026-09-14T00:41:13.246003Z'
assignee: Jason Risch
---

## Description
knot's cc column names each live ticket's connected component: the island of live tickets joined by parents, dependencies and links. The tree page draws parents only, so two epics tangled together by dependencies look independent.

## Design
Colour or label each branch on the tree page by its component, and offer a filter on the tickets page by component, so a reader can see which epics are actually entangled and which can be worked apart. Components come from the listing rows the panel already reads.

## Notes

**2026-09-14T00:41:12.449351Z**

Task completed: each root and parent on the tree page carries an island chip naming knot's connected component, linking to the tickets page filtered by component; Selection gained the component filter, carried through the query string and the summary line, so a reader can see which epics are entangled and which can be worked apart.
