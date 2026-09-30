---
id: kno-01m3qdwrjdbx
title: CI fails when a committed recording differs from a fresh one
status: in_progress
type: task
priority: 2
mode: afk
created: '2026-09-29T20:32:26.700764Z'
updated: '2026-09-30T03:52:35.363611Z'
assignee: Jason Risch
acceptance:
- title: The CI fidelity job fails when a committed recording differs from a fresh recording
  done: false
- title: The recorder can write to a directory other than tests/reading/envelopes
  done: true
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

**2026-09-30T03:45:05.226554Z**

Done in 7d8821c and be908dc:
- The recorder gains --check. It records exactly as a write does, through the same guard, and compares each recording with its committed *.json byte for byte. It names each difference with a diff, each missing or unrecorded file, and the command that re-records.
- CI's fidelity job runs --check as its own named step against the pinned knot.
- The scrub replaces every spelling of the scratch directory anywhere in a recording, longest first.
- A faults probe records check-documents: doc_unknown_ticket and invalid_doc_type with their document ids and paths, and legacy_documents_section with a ticket id. The reader test and the real-knot test both read them.

The first /code-review high found that CI's git name "probe" matched every scrubbed /probe path, so --check would have refused every run. The guard now skips forbidden strings the scrub's placeholders contain. That was reproduced before and after the fix, and the re-review found nothing.

The brainstorm, spec and plan are attached to this ticket as documents.

**2026-09-30T03:52:35.363611Z**

Acceptance criteria ticked as verified: The recorder can write to a directory other than tests/reading/envelopes
