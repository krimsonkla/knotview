---
id: kno-01m2emy7kjzq
title: 'A ticket''s place in its epic: parent and siblings on the ticket page'
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:43.186421Z'
updated: '2026-09-14T00:26:43.311981Z'
assignee: ''
---

## Description
The ticket page lists children and blockers as flat lists, and a child names its parent as one id in the header line. Moving sideways to a sibling means going back to the tree. On the outcry backlog most tasks are children of an epic, so this is the common move.

## Design
When a ticket has a parent, show a breadcrumb with the parent's title, and a card listing the parent's other children with their status and acceptance count, the current one marked. It needs one extra read of the parent per ticket page, which the panel already knows how to do.
