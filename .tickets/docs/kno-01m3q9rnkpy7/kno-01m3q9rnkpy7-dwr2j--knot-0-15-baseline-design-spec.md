---
id: kno-01m3q9rnkpy7-dwr2j
ticket: kno-01m3q9rnkpy7
title: knot 0.15 baseline design spec
type: spec
created: '2026-09-30T00:08:51.078083Z'
updated: '2026-09-30T00:09:25.098809Z'
---

# knot 0.15 baseline Design Spec

**Story:** Move the tests and CI to knot 0.15 (kno-01m3q9rnkpy7)
**Tier:** Feature — test infrastructure and CI change with a bounded scope, no product code
**Brainstorm:** `docs/ai-assistant-ideation/kno-01m3q9rnkpy7-knot-015-baseline-brainstorm.md`

## Changes since last cycle

- The recorder's stages are named: record, normalize, guard, write. The guard runs after the
  existing normalizing of `info` paths and the assignee, not in place of it.
- Empty or missing forbidden strings are dropped before the guard runs.
- The probe writer takes the project's `.knot.edn` text as a parameter, so story 2 can set
  `:required-docs` without forking it. The non-parent documents have named types, and the
  probe is meant to grow.
- The probe module imports neither pytest nor `knotview`. CI only verifies; it never records.
  The unread `KNOT_VERSION` variable in CI is removed.
- R10 is MUST and names the reader test that asserts the recorded version.

## Problem

The recorded knot envelopes and the CI fidelity job describe knot 0.12.0, while the devenv
shell runs 0.15.0. No recording carries a document field, so the epic's later stories would
write readers against shapes nothing records. The recorder also protects recordings from
machine-specific values with a two-field whitelist, which document issues from `check` would
bypass.

## Goal

Every recording, the CI fidelity job and every version reference describe knot 0.15.0, with
documents present in the probe.
**Success signals:** the fidelity test passes against knot 0.15.0 locally and in CI; the suite
passes at 100 percent coverage.

## Scope

**In scope:** the probe project, the recorder, the recordings, the fidelity test's fixture, the
CI fidelity job, version references to knot in tests and CLAUDE.md, and committing the devenv
pin with its lock.
**Out of scope:** any reader of document fields (story 2); `:required-docs` (story 2); live
reload of documents (story 7).
**Non-goals:** changing what the panel renders; changing `devenv.config.toml`.

## Requirements

| ID | Priority | Requirement |
|----|----------|-------------|
| R1 | MUST | One probe definition shared by the recorder and the fidelity test, holding tickets and documents. |
| R2 | MUST | The probe's documents make every listing (`list`, `ready`, `blocked`, `closed`) carry at least one row with `doc_types`, and `list` and `ready` also carry a row without. |
| R3 | MUST | The parent's document ids sort in an order that differs from both their created order and their title order. |
| R4 | MUST | Recordings exist for `document list` on the parent, `document show` on one document, and `document show` on an unknown id. |
| R5 | MUST | No recording is written unless, after normalizing, every string in every recording is free of the scratch directory (both spellings), the recorder's home directory and its git user name. Empty or missing values are not searched for. A failed check writes no file. |
| R6 | MUST | `check-clean.json` is written only when its `issues` list is empty; the clean probe writes a document only when its owner is written. |
| R7 | MUST | All recordings come from knot 0.15.0. |
| R8 | MUST | The CI fidelity job installs knot `v0.15.0` and reports that version. |
| R9 | MUST | `devenv.yaml` pins nix-derivations by commit to `8de06876473302a748efbf76334b5686d11bbce3`, committed with `devenv.lock`. |
| R10 | MUST | The envelopes' docstring, CLAUDE.md, the declared test project and the reader test that asserts the recorded `knot_version` (`tests/reading/test_knot_envelope.py`) name knot 0.15.0. |
| R11 | MUST | The probe writer takes the `.knot.edn` text as a parameter, defaulting to the prefix-only file used today. |

## Design

**Approach:** Documents are written into the probe as files with fixed frontmatter, as the
tickets already are. The recorder runs in four stages: record every envelope into memory,
normalize the fields known to hold machine values (the `info` paths and the assignee, as
today), guard the whole set, and write only if the guard passes. The fidelity test gains the document recordings
through the existing parametrization over `RECORDINGS`.

**Components and responsibilities:**
- *Probe definition* — the ticket files, the document files, and one writer that lays them out
  under a project root with a given `.knot.edn`. Used by the recorder and the fidelity fixture.
  Imports neither pytest nor `knotview`. Later stories extend its documents and config.
- *Recorder* — builds the main and clean probes in one scratch directory, records, guards,
  asserts check-clean is clean, writes.
- *Guard* — a pure check over recorded text and a set of forbidden strings; returns what it
  found. Drops empty forbidden strings. Tested without knot.
- *CI* — installs knot and runs the fidelity test. It verifies and never records.
- *Fidelity test* — unchanged in method; covers the new recordings by parametrization.

**Interfaces and contracts:** a document file is
`<tickets-dir>/docs/<ticket-id>/<doc-id>--<slug>.md` with frontmatter id, ticket, title, type,
created, updated, then a markdown body. The unknown-id recording is an `ok:false` envelope with
code `doc_not_found`.

**Data and state:** the recordings in `tests/reading/envelopes/` are replaced; three are added.
Nothing outside the repository changes.

**Prior art to mirror:** `tests/reading/record_envelopes.py` and the fixture in
`tests/reading/test_real_knot.py` — direct file writing after `knot init`, the prefix-only
`.knot.edn`, and scrubbing `info` paths.

**Key decisions:**
- Documents on the parent (spec and plan), the live child (a spec) and the archived child (an
  `other`); none on the orphan — gives every listing a document row, and two tickets owning a
  spec, which the list filter in story 3 needs.
- Parent ids `pro-01m2aaaaaaaa-d2plan` and `pro-01m2aaaaaaaa-d7spec`, the plan created later and
  titled "Rollout plan", the spec "Design spec" — so no ordering is inherited by accident.
- The guard is a deny-list over every string, and writes happen after it — so an unknown new
  path field cannot leak and a failed run cannot leave a half-replaced fixture set.
- Record the document reads in this story — the fidelity test checks them before any reader
  exists.

**Alternatives rejected:**
- Creating documents with `knot document add` — random ids and current timestamps cannot be
  recorded, and the repository's hooks block direct knot writes.
- Extending the whitelist scrubber — cannot know about fields knot adds later.
- Adding `:required-docs` now — an empty map records nothing checkable; story 2 needs its own.

## Acceptance Criteria

### Story 1: When knot moves to 0.15, I want the recordings to be its answers, so I can write readers against real document shapes.

**AC-1** — shapes present
Given the recorder has run against knot 0.15.0
When the recordings are read
Then `show-parent` has two entries in `data.documents`; each of `list`, `ready`, `blocked` and `closed` has a row with `doc_types`; `list` and `ready` each have a row without; `info` has `paths.docs_path`, `defaults.default_doc_type`, `allowed_values.doc_types`, `allowed_values.required_docs` and `counts.doc_count`; and both check recordings have `scanned.docs`.

**AC-2** — document reads recorded
Given the recorder has run
When `document-list`, `document-show` and `document-not-found` are read
Then the first lists the parent's two documents with created and updated, the second carries a `body`, and the third has `ok` false and code `doc_not_found`.

**AC-3** — the fidelity test checks them
Given knot 0.15.0 is on PATH
When the slow tests run
Then every entry of `RECORDINGS`, including the three new ones, passes the shape check.

**AC-4** — a leak refuses the run
Given a recording contains the scratch directory, the home directory or the git user name
When the guard runs over the set
Then the recorder exits non-zero, names the recording and the string, and writes no file.

**AC-5** — check-clean stays clean
Given the clean probe holds only the parent and the archived child
When `check` runs on it
Then its `issues` list is empty, and a non-empty list refuses the run.

### Story 2: When CI or a maintainer runs the fidelity job, I want it on the same knot as the shell, so I can trust a green result.

**AC-6** — CI version
Given the CI fidelity job runs
When it installs knot
Then `knot --version` reports 0.15.0 and the slow tests pass.

**AC-7** — the pin
Given the devenv shell is entered
When `knot --version` runs
Then it reports 0.15.0, and `devenv.yaml` names commit `8de0687…` of nix-derivations.

**AC-8** — no stale version
Given the change is complete
When the repository is searched outside `.tickets/` and `docs/ai-assistant-ideation/` for `0.12.0`
Then no match remains, including in `tests/reading/test_knot_envelope.py`.

**AC-9** — an absent name does not refuse every run
Given `git config user.name` is empty or unset
When the guard runs
Then that value is not searched for and a clean set passes.

### Traceability
| Story AC | Spec ACs | Requirements | Notes |
|----------|----------|--------------|-------|
| devenv.yaml pins nix-derivations to the PR #16 head, with a comment naming the PR | AC-7 | R9 | PR #16 merged; the pin is its merge commit on main, which supersedes "the PR head" |
| Every recorded envelope comes from knot 0.15.0 and at least one ticket owns documents | AC-1, AC-2, AC-4, AC-5 | R1–R7 | Tightened by the challenger to name every shape |
| The CI fidelity job installs knot v0.15.0 and passes | AC-6 | R8 | |
| The suite passes at 100 percent coverage against the new envelopes | AC-3, AC-8, AC-9 | R5, R7, R10, R11 | |

## Boundaries
- ✅ Always: write probe files directly; run the full suite and the slow tests; keep
  `devenv.config.toml` out of the commit.
- ⚠️ Ask first: changing the shape-comparison rules in the fidelity test.
- 🚫 Never: hand-edit a recording; commit a recording made by a run the guard refused.

## Testing Strategy
| AC | Level | Notes |
|----|-------|-------|
| AC-1, AC-2 | unit | assertions over the recorded files, run without knot |
| AC-3 | integration | slow fidelity test against the real binary |
| AC-4, AC-9 | unit | the guard over sample text, including an empty forbidden string; the refusal path of the recorder |
| AC-5 | unit | an assertion over `check-clean.json`, plus the recorder's own refusal |
| AC-6 | environment | the CI run on the pushed branch |
| AC-7, AC-8 | manual | `knot --version` in the shell; a repository search |

**Not automatable:** AC-6 needs a CI run, verified from the run's log after push.

## Risks and Open Questions
- [Risk] Recording against a different knot than CI installs — mitigated by AC-3 running in
  both places.

## Assumptions
1. The recorder may use `git config user.name` as a forbidden string, so a recorder whose name
   is a common word could refuse spuriously — Impact: LOW
   Correct this if: a maintainer's user name is a substring of legitimate recorded text.

---
After implementing, compare results against each acceptance criterion above
and list any unmet requirements.
