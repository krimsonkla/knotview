---
id: kno-01m2emyc9xnk
title: Removable filter chips on the tickets page
status: in_progress
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:47.997717Z'
updated: '2026-09-14T00:50:51.587918Z'
assignee: Jason Risch
---

## Description
The overview's cards each link to one filter, and the tickets page's summary line names the filters applied, but the only way to drop one filter is to reset the form or edit the URL. Combining two filters from two cards is not possible without the form.

## Design
Show each applied filter as a chip with a remove link that rebuilds the query string without it, using Selection.query_string, and make the overview's cards add to the current selection rather than replace it when the reader arrives with one already applied.
