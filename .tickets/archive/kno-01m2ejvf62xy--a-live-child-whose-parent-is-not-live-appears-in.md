---
id: kno-01m2ejvf62xy
title: A live child whose parent is not live appears in the tree instead of vanishing
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:50:15.490551Z'
updated: '2026-09-13T23:55:39.956761Z'
closed: '2026-09-13T23:55:39.956761Z'
assignee: Jason Risch
---

## Description
Tree.over files a ticket under its parent only when the parent is live, and lists as orphans only tickets with no parent at all, so a live ticket whose parent is closed or absent is in neither place and vanishes from the tree page. Asserted as current behaviour in tests/panel/test_tree.py.

## Design
List such tickets under 'filed under nothing' with a note naming the parent they claim, or under a heading of their own; either way every live ticket appears on the tree page exactly once.

## Notes

**2026-09-13T23:55:39.362113Z**

Task completed: Tree gains strays, the live tickets whose named parent is not live; the tree page lists them under 'filed under a parent that is not live', so every live ticket appears exactly once. Asserted as a value and on the page.
