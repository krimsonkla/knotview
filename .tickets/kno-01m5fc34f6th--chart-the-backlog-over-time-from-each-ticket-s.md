---
id: kno-01m5fc34f6th
title: Chart the backlog over time from each ticket's created and closed instants
status: open
type: feature
priority: 2
mode: hitl
created: '2026-10-21T13:58:26.533131Z'
updated: '2026-10-21T13:58:26.533131Z'
assignee: Jason Risch
tags:
- overview
acceptance:
- title: Open over time, opened and closed, and lead time charts are offered behind the gear and hidden by default
  done: false
- title: A backlog younger than twelve weeks starts at its first ticket's week
  done: false
- title: Charts narrow with the reader's pinned tags
  done: false
---

## Description

The overview gains three charts behind its gear: open tickets at the end of each of the last twelve weeks, tickets opened and closed each week, and the median lead time from created to closed, overall and by type. They are worked out from the created and closed instants knot already reports, so the panel still keeps no history and writes nothing. Past status, priority and type changes are not recorded in the ticket files, so time in progress cannot be charted.
