---
id: kno-01m3qdwrjdbx
title: CI fails when a committed recording differs from a fresh one
status: in_progress
type: task
priority: 2
mode: afk
created: '2026-09-29T20:32:26.700764Z'
updated: '2026-09-30T03:30:14.497638Z'
assignee: Jason Risch
acceptance:
- title: The CI fidelity job fails when a committed recording differs from a fresh recording
  done: false
- title: The recorder can write to a directory other than tests/reading/envelopes
  done: false
---

## Description

The fidelity test compares the shape of each recorded envelope with the real knot's answer, tolerating added keys. A hand-edited recording that changes a value without changing a shape, such as a title or a count, still passes. Raised in the implementation review of kno-01m3q9rnkpy7 and deferred there as a separate mechanism.

## Design

In the CI fidelity job, after the slow tests, run `tests/reading/record_envelopes.py` into a temporary copy of the envelopes directory and fail if any file differs from the committed one. The recorder is byte-stable across runs since kno-01m3q9rnkpy7, so a difference means a recording was edited by hand or knot changed an answer. Only values that change with the date of recording could make it flaky; the primer's stale flag is monotone for the probe's fixed dates, and nothing else in the recordings depends on the date.

## Notes

**2026-09-29T23:30:59.151163Z**

Record a check issue carrying `path`. After kno-01m3q9rx099f the panel reads an integrity issue's `path` (knot 0.15 reports it, absolute, on document issues), but no committed envelope holds an issue with one: the recorded check-issues is an unknown_id issue with `field` and `value` only. The fidelity test cannot notice if knot renames or drops the field until one is recorded. The recorder's scrub must first normalize check issue paths as it does info's, or its guard refuses the recording.

**2026-09-30T03:30:14.497638Z**

Starting work on this task.
