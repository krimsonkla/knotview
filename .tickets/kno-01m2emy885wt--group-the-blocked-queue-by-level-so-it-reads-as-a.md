---
id: kno-01m2emy885wt
title: Group the blocked queue by level, so it reads as a schedule
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:43.844898Z'
updated: '2026-09-14T00:26:43.977865Z'
assignee: ''
---

## Description
knot's level says how many rounds of closing stand before a ticket can start, and the graph guide says level orders work into waves. The blocked page lists tickets flat, so the number is a column rather than a shape.

## Design
On the blocked queue, group rows under headings by level: level 1 as the tickets that become ready once today's ready ones close, level 2 after that, and so on; a level knot gives as null (a cycle) under its own heading naming the integrity check. Keep the flat table on the tickets page.
