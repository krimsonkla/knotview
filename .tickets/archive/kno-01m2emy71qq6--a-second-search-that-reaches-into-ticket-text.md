---
id: kno-01m2emy71qq6
title: A second search that reaches into ticket text
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:42.615188Z'
updated: '2026-09-14T00:53:39.331762Z'
closed: '2026-09-14T00:53:39.331762Z'
assignee: Jason Risch
---

## Description
The search box matches the id, the title and the tags on purpose, and its docstring says why: a match buried in a design section answers with tickets whose titles say nothing about the question. That reason holds, and it still leaves a reader of a 180-ticket backlog with no way to find the ticket that mentions a term only in its body.

## Design
A second field, or a checkbox beside the search, that opts into matching section text; when it is on, each matching row shows the sentence that matched under its title so the reader can see why it is there. It needs the body on listing rows, which knot's list does not carry, so the panel reads each ticket in full only when that search is used and says on the page that it did.

## Notes

**2026-09-14T00:53:38.731335Z**

Task completed: an "in text" checkbox (deep=1) makes the search also match ticket text; the panel then reads each held ticket in full, only when asked, and each matching row shows the first sentence that held the query under its title, so the reader can see why it is there. The shallow search is unchanged.
