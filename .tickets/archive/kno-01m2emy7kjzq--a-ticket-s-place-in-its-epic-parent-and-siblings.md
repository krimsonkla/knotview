---
id: kno-01m2emy7kjzq
title: 'A ticket''s place in its epic: parent and siblings on the ticket page'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:43.186421Z'
updated: '2026-09-14T00:42:45.967862Z'
closed: '2026-09-14T00:42:45.967862Z'
assignee: Jason Risch
---

## Description
The ticket page lists children and blockers as flat lists, and a child names its parent as one id in the header line. Moving sideways to a sibling means going back to the tree. On the outcry backlog most tasks are children of an epic, so this is the common move.

## Design
When a ticket has a parent, show a breadcrumb with the parent's title, and a card listing the parent's other children with their status and acceptance count, the current one marked. It needs one extra read of the parent per ticket page, which the panel already knows how to do.

## Notes

**2026-09-14T00:42:45.275661Z**

Task completed: a child's page opens with a breadcrumb to its parent and shows an 'also under' card listing the parent's other children with their status; a parent that is not live is named without a link (the tree page calls it a stray); the parent is read in full once per page, which is what carries the siblings.
