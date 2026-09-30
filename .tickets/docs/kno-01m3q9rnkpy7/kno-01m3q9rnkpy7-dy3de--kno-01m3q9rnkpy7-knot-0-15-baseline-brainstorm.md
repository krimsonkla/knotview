---
id: kno-01m3q9rnkpy7-dy3de
ticket: kno-01m3q9rnkpy7
title: knot 0.15 baseline brainstorm
type: other
created: '2026-09-30T00:08:57.490853Z'
updated: '2026-09-30T00:09:24.617608Z'
---

# kno-01m3q9rnkpy7 — knot 0.15 baseline brainstorm

Story: kno-01m3q9rnkpy7, "Move the tests and CI to knot 0.15", the first story of epic
kno-01m3q9rmck1r. Date: 2026-09-29. Mode: teams-equivalent, quality-engineer challenger, two
rounds.

## Problem

The recorded envelopes under `tests/reading/envelopes/` and the CI fidelity job are on knot
0.12.0, while the devenv shell now provides 0.15.0. No recording carries a document field, so
the later stories of the epic would be writing readers against shapes nothing records.

## Prior art

`tests/reading/record_envelopes.py` rebuilds a probe project by writing ticket files directly
(`TICKETS`, imported from `tests/reading/test_real_knot.py`), runs every entry of `RECORDINGS`,
scrubs two known machine-specific fields and writes one JSON file per recording. The fidelity
test builds the same probe with its own copy of the writing code and checks each recording's
shape against the binary, tolerating additive keys.

## Approach

Mirror the existing probe: documents are written directly as files, like the tickets, so ids
and timestamps are fixed. The rest is decided as below.

- **One probe module.** `TICKETS`, a new `DOCUMENTS` mapping and one `write_probe(root,
  tickets, documents)` move to `tests/reading/probe.py`. The recorder and the fidelity fixture
  both import it, ending the duplicated writer. A document is written only when its owner is
  among the tickets written.
- **Documents on three tickets.** The parent owns a spec and a plan; the live child owns one;
  the archived child owns one; the orphan owns none. So `list`, `ready`, `blocked` and `closed`
  each carry a `doc_types` row, and `list` and `ready` also carry a row without one. `blocked`
  and `closed` hold one row each in this probe, so they cannot show both.
- **Ids that disagree with every other order.** The parent's plan has id `...-d2plan` and was
  created after the spec, id `...-d7spec`; by title the spec sorts first. So knot's id order
  disagrees with created order and title order, and story 2 must choose an ordering rather than
  inherit one by accident. Story 1 asserts no order.
- **Record the document reads now.** `document list` on the parent, `document show` on the spec,
  and `document show` on an unknown id (`doc_not_found`). The fidelity test parametrizes over
  `RECORDINGS`, so they are checked against the binary with no reader present yet.
- **A guard, not a whitelist, keeps recordings clean.** Every envelope is recorded into memory
  first. A guard then walks every string in every recording and refuses the run if any contains
  the scratch directory (in both spellings), the recorder's home directory, or its git user name.
  Only a run that passes writes files, so a failed run leaves the fixtures untouched. The guard
  has its own fast test that runs without knot.
- **check-clean stays clean.** The clean probe filters documents with their owners, and the
  recorder refuses to write `check-clean.json` unless its `issues` list is empty.
- **No `:required-docs` yet.** An empty map records nothing worth checking; story 2 adds a
  probe or recording that sets it.
- **Version references move.** The CI fidelity job installs `--git/tag v0.15.0` and sets
  `KNOT_VERSION: v0.15.0`. The envelopes' docstring, CLAUDE.md, the declared test project's
  `knot_version` and the reader test that reads it name 0.15.0.
- **The devenv pin lands in the same commit as its lock.** `devenv.yaml` pins the merge commit
  of nix-derivations#16, `8de0687`, which is the head of that repo's main. `devenv.config.toml`
  is the developer's own change and stays out of this story.

## What the challenger changed

Round 1 raised two P0s, four P1s and two P2s; round 2 confirmed each answered, withdrew the
devenv P1 on a verified fact, and added one P1 (write only after the guard passes), adopted
above.

- The scrubber was a two-field whitelist; a document issue from `check` carries an absolute
  path outside it. Now a deny-list guard over every string.
- A clean probe that filters tickets by name would orphan a document, which knot reports as an
  error, making `check-clean` dirty. Now documents filter with their owners and emptiness is
  asserted.
- `blocked` had no document-bearing row; the live child now owns one.
- Fixed ids could happen to sort in the reader's preferred order; the chosen ids disagree with
  both alternatives.
- The criterion "at least one ticket owns documents" was too weak; it now names every shape.

## Deferred

A document edit under the default docs directory already moves the live digest, since the
digest walks every markdown file under the tickets directory. This story does not claim or
assert that; story 7, kno-01m3q9rx099f, owns it.
