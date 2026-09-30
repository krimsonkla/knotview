---
id: kno-01m3qdwrjdbx-drrr6
ticket: kno-01m3qdwrjdbx
title: Re-record check brainstorm
type: other
created: '2026-09-30T03:45:03.498423Z'
updated: '2026-09-30T03:45:03.498423Z'
---

# Re-record check brainstorm

Story: kno-01m3qdwrjdbx, "CI fails when a committed recording differs from a fresh one". Date:
2026-09-30. Mode: teams-equivalent, quality-engineer challenger, two rounds.

## Problem

The fidelity test compares the shapes of the recorded envelopes with the real knot's answers, so a
hand-edited value passes. And no recording holds a check issue with a `path`, which the panel now
reads.

## Approach

- **`--check` on the recorder.** It records and scrubs as now, then goes through the same
  `finish()` with a writer that compares instead of writing. It reports each differing file with a
  unified diff, each committed file no recording produces, and each recording with no committed
  file, then prints the re-record command and exits 1. It cannot write.
- **The scrub replaces every spelling of the scratch root with /probe throughout a recording,**
  longest spelling first, since on macOS the resolved spelling contains the created one.
- **The guard stays.** It now catches spellings the scrub did not know, and it is the last thing
  between a machine path and a committed fixture.
- **A third probe records `check-documents`:** the clean probe plus one document with an undeclared
  type, giving an invalid_doc_type issue with ids and path. It sits outside the clean-check rule.
  The reader and fidelity tests assert it becomes an issue linking the document, shown from /probe.
- **CI runs `--check` as its own named step** in the fidelity job, after the slow tests. It shares
  that job's pinned knot, version assertion and git identity.

## What the challenger changed

- Replacement order: a set of spellings iterates in hash order, and the short one first leaves
  /private/probe.
- The check needs the fidelity job's knot and git identity, so it is a step there, not a job.
- The guard is kept and its narrower, more important job said.
- Date dependence is accepted: the primer's stale flag is monotone, and nothing else moves.
