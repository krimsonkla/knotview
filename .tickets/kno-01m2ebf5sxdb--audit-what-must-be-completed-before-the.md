---
id: kno-01m2ebf5sxdb
title: Audit what must be completed before the repository is made public
status: in_progress
type: task
priority: 2
mode: hitl
created: '2026-09-13T21:41:12.637442Z'
updated: '2026-09-13T23:27:55.843323Z'
assignee: Jason Risch
deps:
- kno-01m2ebf3c8mx
- kno-01m2ebf3w4q3
---

## Description
The repository is private and is to be made public. Before that happens an agent workflow reviews the code and lists what must be completed first. This ticket holds that audit and its findings.

Known before the audit runs: the coverage gate fails, four lint findings fail the hooks, CLAUDE.md is a stub with empty Architecture, Key Files, Conventions and Gotchas sections, and there is no LICENSE, no CONTRIBUTING and no CI.

## Design
Run the review workflow over the initial commit once the coverage and lint tickets have closed, so the agents are reading the code that will ship rather than the code that will be refactored. Record each finding as a child ticket of this one, and close this one when the list is complete rather than when the findings are done.

## Notes

**2026-09-13T23:19:46.596719Z**

Starting work on this task: running the pre-public review workflow over main at fcc6b66.

**2026-09-13T23:27:55.843323Z**

Audit complete: the review workflow ran six lenses (legal, docs, security, packaging, hygiene, tests) over main at fcc6b66 with one adversarial verifier per finding; 53 agents. 49 raw findings, 47 after dedup, 46 confirmed, 1 refuted. The 46 overlap heavily across lenses and are filed as 24 child tickets, each carrying every lens's evidence and recommendation. Two are P0 (no licence; the dev shell depends on a private git+ssh input), six P1, sixteen P2.

Refuted, not filed: devenv input krimsonkla/nix-derivations is public but carries no licence (legal): Refuted. I confirmed the evidence chain as far as it goes: /Users/krimsonkla/git/krimsonkla/knotview/devenv.yaml:18 declares `nix-derivations: url: github:krimsonkla/nix-derivations`, devenv.lock references it at lines 171/214 (devenv-layers pulls it in too), and `gh api repos/krimsonkla/nix-derivations` does return `license: NOASSERTION / "Other"`. But the conclusion "carries no licence" is wrong: `gh api repos/krimsonkla/nix-derivations/contents` lists a top-level LICENSE file, and decoding it shows a full MIT License, Copyright (c) 2026 krimsonkla, prefixed by a one-line scoping note ("This license covers the packaging expressions in this repository only. Packaged upstream sources and patches retain their own licenses."). That preamble is exactly what defeats GitHub's licensee template matcher, hence NOASSERTION; the repository is nonetheless clearly and permissively licensed, so knotview's dev environment does not depend on an unlicensed repo. The only residual item is cosmetic (GitHub's licence badge won't render; moving the scoping note to README or below the MIT text would fix detection), which is not a knotview issue and does not block going public.

Lens coverage statements and the full result are kept with the workflow run wf_93012288-758.
