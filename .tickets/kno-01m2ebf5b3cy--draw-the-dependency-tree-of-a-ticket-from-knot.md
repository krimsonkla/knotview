---
id: kno-01m2ebf5b3cy
title: Draw the dependency tree of a ticket from knot dep tree
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T21:41:12.163057Z'
updated: '2026-09-13T21:41:12.273808Z'
assignee: ''
---

## Description
The tree page draws what is filed under what, from `parent`. It does not draw the dependency graph, which is the other tree knot holds and the one that decides what is ready. `knot dep tree <id> --json` is a read this panel does not run.

## Design
Add `dep tree` to the declared READS. On a ticket page, render its deps subtree from that command's recursive node shape, marking `missing` and `seen_before` nodes as knot reports them. Keep the parent tree as it is; the two answer different questions.
