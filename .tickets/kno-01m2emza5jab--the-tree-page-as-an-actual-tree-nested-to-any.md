---
id: kno-01m2emza5jab
title: 'The tree page as an actual tree: nested to any depth, foldable, each ticket once'
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:27:18.578132Z'
updated: '2026-09-14T00:27:18.732748Z'
assignee: ''
---

## Description
The tree page is a list of cards, one per parent, each holding a flat table of children, followed by strays and orphans. It shows what is filed under what, but not as a tree: a child that is itself a parent appears twice, once as a row and once as its own card, and nothing on the page shows depth. The outcry backlog has epics under epics, and the reader wants to see the shape at a glance.

## Design
Draw the parents as a real nested tree: one node per ticket, children indented under their parent to any depth, each node showing its status chip, title, acceptance count and its own children count, with a fold control per node so a large epic can be collapsed and the page remembers which nodes are folded in the browser's own storage. A ticket appears exactly once, under the deepest parent that holds it; strays and orphans stay as their own sections at the bottom. Build the nesting in Tree.over from the parent field the listing already carries, keep the tickets table for the flat views, and assert on the page that a grandchild renders under its parent and that every live ticket appears once. No writes: folding is per viewer.
