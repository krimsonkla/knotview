---
id: kno-01m2ehjh2cd5
title: '[P2] No documented or scripted way to re-record the envelope fixtures'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:53.932025Z'
updated: '2026-09-13T23:48:40.685613Z'
closed: '2026-09-13T23:48:40.685613Z'
assignee: Jason Risch
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the tests lens and confirmed by an adversarial verifier.

### From the tests lens: No documented or scripted way to re-record the envelope fixtures

Evidence: tests/reading/envelopes/__init__.py docstring (lines 1-7) explains provenance well (knot 0.12.0, a probe project with a parent, two children, an orphan, etc.) and names test_real_knot.py as the check. But the probe's ticket files exist only as the TICKETS dict inside tests/reading/test_real_knot.py (lines 23-108), scripts/ is empty and untracked, and grep across tests/, docs/ and README for "re-record"/"regenerat" finds nothing. When knot ships a new schema the shape test fails and a contributor has to reverse-engineer the recording procedure from the test body.

Recommendation: Add a short recipe to the envelopes docstring or a `scripts/record_envelopes.py` that reuses test_real_knot's TICKETS and the parametrized (name, verb) table to rewrite tests/reading/envelopes/*.json, and mention the knot version to bump in the docstring.

Verifier (P2, blocks public: no): Reproduced. tests/reading/envelopes/__init__.py (lines 1-7) documents provenance (knot 0.12.0, the probe's ticket mix) but no recording recipe; the probe's ticket files exist only as the TICKETS dict in tests/reading/test_real_knot.py, whose fixture writes them directly under .tickets/ after `knot init` and patches .knot.edn to prefix "pro". scripts/ is an empty, untracked directory (git ls-files scripts/ returns nothing), docs/ holds only ai-assistant-ideation/, there is no README mention, and grep for "re-record"/"regenerat" across tests/, docs/ and README finds nothing. One extra wrinkle the reporter missed: check-clean.json is not in the parametrized table at all, so it is neither shape-checked nor re-derivable from the test. Still, the procedure is recoverable in a few minutes by reading the probe fixture and raw() helper (run `knot <verb> --json` in the probe and dump stdout), and it only bites when knot changes its envelope schema, so this is polish rather than something a first contributor hits: P2, does not block going public.

## Notes

**2026-09-13T23:48:40.084926Z**

Task completed: tests/reading/record_envelopes.py rebuilds the probe project the fidelity test uses, records every envelope in RECORDINGS (now shared with the fidelity test) plus a clean check from a second probe, pretty-prints them, and scrubs the machine path and the assignee. Documented in the envelopes package docstring and CONTRIBUTING.
