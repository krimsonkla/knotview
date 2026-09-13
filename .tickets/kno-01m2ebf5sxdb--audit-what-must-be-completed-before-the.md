---
id: kno-01m2ebf5sxdb
title: Audit what must be completed before the repository is made public
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T21:41:12.637442Z'
updated: '2026-09-13T21:41:21.962335Z'
assignee: ''
deps:
- kno-01m2ebf3c8mx
- kno-01m2ebf3w4q3
---

## Description
The repository is private and is to be made public. Before that happens an agent workflow reviews the code and lists what must be completed first. This ticket holds that audit and its findings.

Known before the audit runs: the coverage gate fails, four lint findings fail the hooks, CLAUDE.md is a stub with empty Architecture, Key Files, Conventions and Gotchas sections, and there is no LICENSE, no CONTRIBUTING and no CI.

## Design
Run the review workflow over the initial commit once the coverage and lint tickets have closed, so the agents are reading the code that will ship rather than the code that will be refactored. Record each finding as a child ticket of this one, and close this one when the list is complete rather than when the findings are done.
