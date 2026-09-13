---
id: kno-01m2ebf4tyvf
title: Read knot prime for the ready-to-close set and stale in-progress work
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T21:41:11.646254Z'
updated: '2026-09-13T21:41:11.790046Z'
assignee: ''
---

## Description
`knot prime` is a read this panel never runs. It reports two things nothing else does: `ready_to_close`, the active tickets whose every acceptance criterion is checked, and `stale: true` on in-progress tickets untouched for fourteen days. Both are the questions a person opening a panel asks first.

## Design
Add `prime` to the declared READS. Show a "ready to close" group and a stale marker on the overview, sourced from prime's JSON rather than recomputed here, so the panel agrees with what the CLI tells an agent.
