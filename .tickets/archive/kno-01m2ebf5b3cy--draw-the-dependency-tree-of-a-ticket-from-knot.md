---
id: kno-01m2ebf5b3cy
title: Draw the dependency tree of a ticket from knot dep tree
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T21:41:12.163057Z'
updated: '2026-09-14T00:03:38.028309Z'
closed: '2026-09-14T00:03:38.028309Z'
assignee: Jason Risch
---

## Description
The tree page draws what is filed under what, from `parent`. It does not draw the dependency graph, which is the other tree knot holds and the one that decides what is ready. `knot dep tree <id> --json` is a read this panel does not run.

## Design
Add `dep tree` to the declared READS. On a ticket page, render its deps subtree from that command's recursive node shape, marking `missing` and `seen_before` nodes as knot reports them. Keep the parent tree as it is; the two answer different questions.

## Notes

**2026-09-14T00:03:37.409376Z**

Task completed: "dep tree" is one of the reads (two words, so knot's writing dep verb stays outside READS); Dependency is the recursive node with knot's missing and seen_before flags; KnotCommand.dependencies, the Backlog port and the declared backlog carry it; the ticket page draws the tree all the way down with a missing leaf shown as such and a node drawn above marked. Recorded dep-tree.json backs the reader test; the fidelity test covers the shape.
