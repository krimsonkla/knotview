---
id: kno-01m3qdwrjdbx-d5zkk
ticket: kno-01m3qdwrjdbx
title: Re-record check implementation plan
type: plan
created: '2026-09-30T03:45:03.868511Z'
updated: '2026-09-30T03:45:03.868511Z'
---

# Re-record check implementation plan

**Goal:** CI fails on any drift between the committed recordings and a fresh one, and a check
issue with a path is recorded. **Spec:** `kno-01m3qdwrjdbx-rerecord-check-spec.md`. **Test route:**
strict.

## Task 1: The scrub
- [ ] Failing test: `scrubbed()` over a text holding both spellings, given in either order,
  yields /probe for both.
- [ ] `scrubbed(name, text, roots)`: replace each spelling of the root, sorted by length
  descending, throughout the text before parsing; then the assignee rule for info. The
  info-paths prefix loop goes, since the text replacement covers it.
- [ ] `forbidden_strings` docstring: the guard's remaining job.

## Task 2: --check
- [ ] Failing tests of `compared(recordings, committed)`: equal gives no problems; a differing
  file gives its unified diff; a missing or extra file is named.
- [ ] `compared(recordings, committed) -> list[str]` and `main(argv)`: `--check` builds the
  recordings and runs `finish()` with a writer that writes nothing, then compares the recordings
  with HERE's `*.json` itself, prints problems and the re-record command, and returns 1 on any;
  otherwise it writes as now.
- [ ] Before Task 3: `--check` over the unchanged corpus reports no difference, proving the new
  scrub reproduces every committed file.

## Task 3: check-documents
- [ ] `write_faults(root)`: the clean tickets with a Documents heading in the parent's body, a
  `memo` document, and an orphan document written after the probe. Record `check` there as
  `check-documents`. A comment says it is outside the clean-check rule.
- [ ] Record it (`uv run python -m tests.reading.record_envelopes`) and commit the file.
- [ ] Reader test: `_issue` over the recorded issue, with root /probe, gives document ids
  `("pro-01m2aaaaaaaa-d5memo",)` and a shown path under `.tickets/docs/`. Comment on the /probe
  coupling between info and this probe.
- [ ] test_real_knot: the binary's check over the same probe gives the same code, id and shown path.

## Task 4: CI and gate
- [ ] ci.yml: a step named "the committed recordings match a fresh recording from the pinned knot"
  running `uv run python -m tests.reading.record_envelopes --check`, after the slow tests.
- [ ] Gate: pytest, ruff, black, pylint, prek; run `--check` locally; push and read CI.
