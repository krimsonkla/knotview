---
id: kno-01m3q9rnkpy7
title: Move the tests and CI to knot 0.15
status: closed
type: task
priority: 2
mode: afk
created: '2026-09-29T19:20:18.294550Z'
updated: '2026-09-29T20:43:55.250711Z'
closed: '2026-09-29T20:43:55.250711Z'
assignee: Jason Risch
parent: kno-01m3q9rmck1r
acceptance:
- title: 'devenv.yaml pins nix-derivations to the PR #16 head, with a comment naming the PR'
  done: true
- title: Every recorded envelope comes from knot 0.15.0 and at least one ticket in the fixture owns documents
  done: true
- title: The CI fidelity job installs knot v0.15.0 and passes
  done: true
- title: The suite passes at 100 percent coverage against the new envelopes
  done: true
---

## Description

knotview's devenv already pins knot 0.15.0 from krimsonkla/nix-derivations#16, uncommitted. The recorded envelopes under `tests/reading/envelopes/` and the CI fidelity job still use knot 0.12.0, so no test sees a document field. Move everything to 0.15.0 before any document work lands, so the tests describe the knot the panel runs against.

## Design

Commit the devenv pin with a note to move back to the default branch once the PR merges. Re-record every envelope with `tests/reading/record_envelopes.py` from a fixture project that owns documents, so `show`, the listings, `info` and `check` all carry document fields. Move the CI fidelity job's `--git/tag` and `KNOT_VERSION` to v0.15.0.

## Notes

**2026-09-29T19:24:58.926259Z**

Starting work on this task.

**2026-09-29T20:36:49.031805Z**

Implementation artifacts attached
branch: jr/kno-01m3q9rmck1r-attached-documents commit: 6258e34f5558a024ec2b17bc56180fb683479fdf
- Brainstorm: docs/ai-assistant-ideation/kno-01m3q9rnkpy7-knot-015-baseline-brainstorm.md @ 6258e34f5558a024ec2b17bc56180fb683479fdf
- Spec: docs/ai-assistant-ideation/kno-01m3q9rnkpy7-knot-015-baseline-spec.md @ 6258e34f5558a024ec2b17bc56180fb683479fdf
- Plan: docs/ai-assistant-ideation/kno-01m3q9rnkpy7-knot-015-baseline-plan.md @ 6258e34f5558a024ec2b17bc56180fb683479fdf

**2026-09-29T20:43:53.108199Z**

Task completed: the recorded envelopes come from knot 0.15.0, and the probe's tickets own four documents (a spec and a plan on the parent, a spec on the live child, a note on the archived child), so show, every listing, info and both checks carry document fields. Three new recordings cover document list, document show and an unknown document. The probe is one module shared by the recorder and the fidelity test. The recorder records every envelope, normalizes info's paths and assignee, then refuses to write anything if a recording still holds the scratch directory, the home directory or the git name, or if the clean check reports an issue; the forbidden set and the refusal are tested without knot. The recorder writes four-space JSON and the recordings are excluded from prettier, so two recordings in a row are byte-identical.

The criteria as met: the devenv pin is the merge commit of nix-derivations#16 (8de0687, the head of its main), not the PR head the first criterion names, because the PR merged during the story. The second criterion was tightened in review to name every document shape; all are asserted in tests/reading/test_recorded_documents.py. CI run 36628225854 on PR #6 installed knot v0.15.0 at its pinned commit 9956d45, the new step confirmed `knot --version` is 0.15.0, and all 15 fidelity tests passed. The suite passes at 100 percent.

Also: the primer now marks the probe's child stale, because its fixed last update is more than 14 days before the recording; the two primer tests expect it. Main had moved on with pinned CI installs; the branch merges it and pins knot's commit for v0.15.0. Deferred: a CI check that re-records and diffs, filed as kno-01m3qdwrjdbx.

**2026-09-29T20:43:54.163052Z**

Acceptance criteria ticked as verified: devenv.yaml pins nix-derivations to the PR #16 head, with a comment naming the PR, Every recorded envelope comes from knot 0.15.0 and at least one ticket in the fixture owns documents, The CI fidelity job installs knot v0.15.0 and passes, The suite passes at 100 percent coverage against the new envelopes
