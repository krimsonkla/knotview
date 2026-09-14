---
id: kno-01m2emyb4fcv
title: Hide a table column whose every value is the same
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:46.799738Z'
updated: '2026-09-14T00:26:46.925129Z'
assignee: ''
---

## Description
On a backlog that assigns nothing, every row of every table reads 'nobody' under assignee, and on one that uses one mode every row reads 'hitl'. A column with one value across the table carries no information and takes room from the title.

## Design
When every row of a table carries the same value for assignee or mode, drop the column and say the value once above the table ('all unassigned'). The tickets page keeps the column when a filter on that field is applied, since the reader is looking at it.
