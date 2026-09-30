---
id: kno-01m3qdwrjdbx-d9q7n
ticket: kno-01m3qdwrjdbx
title: Re-record check design spec
type: spec
created: '2026-09-30T03:45:03.680014Z'
updated: '2026-09-30T03:45:03.680014Z'
---

# Re-record check design spec

**Story:** CI fails when a committed recording differs from a fresh one (kno-01m3qdwrjdbx)
**Tier:** Feature — the recorder, its scrub, one recording, one CI step

## Problem

A hand-edited recording that keeps its shape passes CI, and no recording holds a check issue with
a path, the field the integrity card reads.

## Design

**Approach:** `--check` records exactly as a write does and goes through the same `finish()` guard
with a writer that writes nothing, then compares the recordings with the committed `*.json` in the
envelopes directory (the package's `__init__.py` and `__pycache__` beside them are not fixtures).

**The scrub.** It used to rewrite only info's `paths` values by prefix. knot also writes absolute
paths into a check issue's `path` and `message`, so recording a document issue needs the scrub to
reach them: it now replaces every spelling of the scratch directory throughout a recording's raw
text, before parsing, longest spelling first. That edits text nobody enumerated, which is why the
leak guard stays: it is the last check for a spelling the scrub did not know.

**Key decisions:** the check is a step in the fidelity job, sharing its pinned knot, version check
and git identity; a separate faults probe records check-documents, with two document issues the
panel links and one ticket issue it must not.

## Requirements

| ID | Priority | Requirement |
|----|----------|-------------|
| R1 | MUST | `python -m tests.reading.record_envelopes --check` records and scrubs every envelope and compares each with its committed file, writing nothing. |
| R2 | MUST | It exits 1 when any recording differs (printing a unified diff), a committed file has no recording, or a recording has no committed file, and prints the command that re-records; else 0. |
| R3 | MUST | The scrub replaces every spelling of the scratch root with /probe anywhere in a recording, longest spelling first, so the result does not depend on iteration order. |
| R4 | MUST | The leak guard stays, documented as the last check for spellings the scrub does not know. |
| R5 | MUST | A `check-documents` recording, from a probe with three faults, holds doc_unknown_ticket and invalid_doc_type issues with their document ids and paths under /probe, and a legacy_documents_section issue with a ticket id; it is outside the clean-check rule. |
| R6 | MUST | The reader turns that recording into an issue linking its document, with the path shown from the project root; the fidelity test asserts the same against the binary. |
| R7 | MUST | CI's fidelity job runs `--check` as its own named step after the slow tests, with the job's pinned knot and git identity. |

## Acceptance Criteria

**AC-1** — Given recordings equal to the committed files, when `--check` runs, then it exits 0 and
no file changes.
**AC-2** — Given a recording differing from its committed file, when `--check` runs, then it exits
1, names the file with a diff and the re-record command, and no file changes.
**AC-3** — Given a committed file no recording produces, or a recording with no committed file,
when `--check` runs, then it exits 1 naming it.
**AC-4** — Given a text holding both /private/tmp/x/probe and /tmp/x/probe, when scrubbed, then
both read /probe.
**AC-5** — Given the committed check-documents recording, when read, then the two document issues
link their documents and show their paths from /probe, and the legacy issue links nothing.
**AC-6** — Given the real knot, when the fidelity test runs over the same faults, then the issues
read the same way.

## Boundaries
- 🚫 Never: let `--check` write; drop the leak guard.
