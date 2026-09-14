---
id: kno-01m2emy8t442
title: Show connected components on the tree page
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:44.420420Z'
updated: '2026-09-14T00:26:44.547030Z'
assignee: ''
---

## Description
knot's cc column names each live ticket's connected component: the island of live tickets joined by parents, dependencies and links. The tree page draws parents only, so two epics tangled together by dependencies look independent.

## Design
Colour or label each branch on the tree page by its component, and offer a filter on the tickets page by component, so a reader can see which epics are actually entangled and which can be worked apart. Components come from the listing rows the panel already reads.
