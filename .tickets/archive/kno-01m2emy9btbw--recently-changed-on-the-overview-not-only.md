---
id: kno-01m2emy9btbw
title: Recently changed on the overview, not only recently closed
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:44.986345Z'
updated: '2026-09-14T00:45:45.749255Z'
closed: '2026-09-14T00:45:45.749255Z'
assignee: Jason Risch
---

## Description
The overview shows what closed recently. A reader following an agent asks a different question: what is it touching now. knot bumps a ticket's updated instant on every save, so the answer is in data the panel already reads.

## Design
A 'recently changed' card on the overview listing the live tickets by updated instant, newest first, capped like the closed list, with the instant shown relative (minutes ago, today, yesterday) as well as absolute on hover.

## Notes

**2026-09-14T00:45:45.107571Z**

Task completed: the overview has a 'recently changed' card listing live tickets by knot's updated instant, newest first, capped like the closed list, each with a coarse relative time (just now, minutes, hours, days) and the exact instant on hover.
