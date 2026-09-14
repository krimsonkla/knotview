---
id: kno-01m2emy6fkk6
title: Show a ticket's notes as a timeline, newest first
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:42.035711Z'
updated: '2026-09-14T00:35:49.056211Z'
closed: '2026-09-14T00:35:49.056211Z'
assignee: Jason Risch
---

## Description
knot appends every note under one heading with a bold timestamp above it. The ticket page shows that section as one block, oldest first, so the latest state of an epic is at the bottom of a long card. On the outcry backlog the research-store epic has seven notes and the reader wants the last one.

## Design
Split the notes section on knot's timestamp lines, show each note as an entry with its instant as the heading (humanised, with the full instant on hover), newest first, and keep the rendering shared with the markdown story. A note that carries no timestamp (an old hand-written one) is shown as it is at the end.

## Notes

**2026-09-14T00:35:48.400758Z**

Task completed: Ticket.timeline splits the notes section on the bold instants knot writes above each note and returns them newest first, a hand-written note without an instant keeping its place; the ticket page shows them as a timeline with the humanised instant as each heading and the full instant on hover. Asserted as a value and on the page.
