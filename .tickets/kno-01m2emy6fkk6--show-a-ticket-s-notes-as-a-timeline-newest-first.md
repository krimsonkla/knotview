---
id: kno-01m2emy6fkk6
title: Show a ticket's notes as a timeline, newest first
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:42.035711Z'
updated: '2026-09-14T00:26:42.174852Z'
assignee: ''
---

## Description
knot appends every note under one heading with a bold timestamp above it. The ticket page shows that section as one block, oldest first, so the latest state of an epic is at the bottom of a long card. On the outcry backlog the research-store epic has seven notes and the reader wants the last one.

## Design
Split the notes section on knot's timestamp lines, show each note as an entry with its instant as the heading (humanised, with the full instant on hover), newest first, and keep the rendering shared with the markdown story. A note that carries no timestamp (an old hand-written one) is shown as it is at the end.
