---
id: kno-01m2ehj3b95z
title: '[P0] No LICENSE file and no licence metadata anywhere'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:39.881162Z'
updated: '2026-09-13T23:33:20.597523Z'
closed: '2026-09-13T23:33:20.597523Z'
assignee: Jason Risch
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P0, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the docs, hygiene, legal, security, tests lenses and confirmed by an adversarial verifier.

### From the docs lens: No LICENSE file and no license metadata anywhere

Evidence: `ls /Users/krimsonkla/git/krimsonkla/knotview | grep -i licen` returns nothing; `git ls-files` lists no LICENSE/COPYING; `grep -n -i license pyproject.toml README.md` returns nothing. pyproject.toml [project] has no `license` field and no license classifier. The audit ticket .tickets/kno-01m2ebf5sxdb--audit-what-must-be-completed-before-the.md itself records 'there is no LICENSE'.

Recommendation: Add a LICENSE file at the repo root, set `license = {text = "..."}` (or `license-files`) and the matching classifier in pyproject.toml, and name the license in README. Without it the code is all-rights-reserved and nobody outside may legally use or contribute to it.

Verifier (P0, blocks public: yes): Could not refute it. At fcc6b66 in /Users/krimsonkla/git/krimsonkla/knotview: `ls -a | grep -i -E 'licen|copying'` returns nothing; `git ls-files | grep -i -E 'licen|copying|notice'` returns nothing; `grep -n -i -E 'licen|classifier' pyproject.toml README.md` only hits the `classifiers = [` line, and the [project] table has no `license`/`license-files` field and its five classifiers contain no `License ::` entry; a repo-wide `git grep -i` for license/SPDX outside .tickets returns nothing, so there is no license header in any source file either; and the audit ticket itself states at line 19 "there is no LICENSE". With no grant anywhere, the default under copyright is all-rights-reserved, which means outside users cannot legally run, fork, or contribute to a public repo and PyPI metadata would be unlicensed, so P0 and blocks_public=true are correct. The fix is small (LICENSE file, `license` field plus classifier in pyproject.toml, one line in README) but it is a prerequisite, not polish.

### From the hygiene lens: No LICENSE file and no licence metadata

Evidence: `git ls-files | grep -i -E "license|copying"` returns nothing; `ls LICENSE* COPYING*` -> "No such file or directory". pyproject.toml:5-17 has classifiers but no `license` field or `License ::` classifier. The audit ticket (.tickets/kno-01m2ebf5sxdb...md:19) already lists "no LICENSE, no CONTRIBUTING and no CI" as known.

Recommendation: Add a LICENSE file at the repo root, add `license = {text = "..."}` (or the SPDX `license = "..."`) and the matching classifier to pyproject.toml, and state the licence in README.md. Without it the code is all-rights-reserved regardless of being public.

Verifier (P0, blocks public: yes): Confirmed at fcc6b66: `git ls-files | grep -iE "license|copying|licence"` returns nothing and `ls LICENSE* COPYING* LICENCE*` all fail; pyproject.toml [project] (lines 5-17) carries name/version/description/readme/classifiers but no `license` key and no `License ::` classifier; grep for licence/copyright/MIT/Apache/GPL across README.md and pyproject.toml is empty; and the audit ticket's own Description (.tickets/kno-01m2ebf5sxdb...md) already records "no LICENSE, no CONTRIBUTING and no CI" as known. Severity P0 is correct: a public repository with no licence is all-rights-reserved by default, so nobody can legally use, fork or contribute to it, and the packaging metadata would ship without a licence declaration as well. The fix is small (LICENSE file, `license` field plus classifier in pyproject.toml, a line in README.md) but it must precede flipping the repo public. Not related to the coverage gate or the lint findings.

### From the legal lens: No licence anywhere: no LICENSE file, no license field in pyproject, README silent

Evidence: `ls LICENSE* COPYING* NOTICE*` in /Users/krimsonkla/git/krimsonkla/knotview → "No such file or directory". /Users/krimsonkla/git/krimsonkla/knotview/pyproject.toml [project] (lines 5-16) has name, version, description, readme, requires-python and classifiers but no `license`, no `license-files`, and no `License ::` classifier. /Users/krimsonkla/git/krimsonkla/knotview/README.md contains no licence statement. `git log --all --name-only` shows no licence file ever committed.

Recommendation: Before the repo goes public, add a LICENSE file (MIT matches knot, which is MIT, and every runtime dependency is MIT/BSD/PSF, so nothing constrains the choice), add `license = "MIT"` and `license-files = ["LICENSE"]` under [project] in pyproject.toml, and add a one-line Licence section to README.md. Without a licence a public GitHub repo is all-rights-reserved and outsiders may not legally use, modify or redistribute it.

Verifier (P0, blocks public: yes): Could not refute it; every piece of evidence reproduces. `ls LICENSE* COPYING* NOTICE*` in /Users/krimsonkla/git/krimsonkla/knotview returns "No such file or directory" for all three; /Users/krimsonkla/git/krimsonkla/knotview/pyproject.toml's [project] table (lines 5-16) has name, version, description, readme, requires-python and five classifiers but no `license`, no `license-files`, and no `License ::` classifier; `grep -in licen README.md` returns nothing; `git log --all --name-only` across all 18 commits shows no LICENSE/COPYING/NOTICE ever committed; and a repo-wide grep for SPDX/Copyright headers in source finds none, so there is no per-file licence grant to fall back on either. The only mention of a licence in the whole tree is the audit ticket itself (.tickets/kno-01m2ebf5sxdb line 19), which already acknowledges "there is no LICENSE" as a known pre-audit gap, so the finding is confirmed rather than contradicted by the project's own records. P0 is right: a public repository with no licence is all-rights-reserved by default, so the very act of making it public invites use that nobody is permitted to make, and unlike a contributor-experience gap (P1) or polish (P2) it cannot be deferred to after publication without a legal exposure window. Fix is trivial (LICENSE file, `license`/`license-files` in pyproject, one README line) but it must land before the visibility flip.

### From the security lens: No license file or license metadata

Evidence: `ls LICENSE* COPYING*` in /Users/krimsonkla/git/krimsonkla/knotview: no such file. `git ls-files` lists no LICENSE. /Users/krimsonkla/git/krimsonkla/knotview/pyproject.toml has no `license`, `authors` or `[project.urls]` field (grep for license|authors|urls returned nothing). Without a license, outside users have no right to copy, modify or run the code.

Recommendation: Add a LICENSE file at the repository root and a matching `license = {text = "..."}` (or SPDX `license = "MIT"`) plus `authors` in pyproject.toml before the repository is made public.

Verifier (P0, blocks public: yes): Reproduced in full at /Users/krimsonkla/git/krimsonkla/knotview (main, fcc6b66): `ls LICENSE* COPYING* LICENCE*` finds nothing; `git ls-files | grep -iE 'licen|copying'` returns nothing across the 94 tracked files; /Users/krimsonkla/git/krimsonkla/knotview/pyproject.toml's [project] table carries name, version, description, readme, requires-python, classifiers and dependencies but no `license`, `authors`, `[project.urls]` or a `License ::` classifier; and a grep for license/copyright/SPDX over tracked .py/.md/.toml/.nix/.yaml sources (excluding .tickets/) is empty, so there is no in-source or README notice either. With no grant, the code is all-rights-reserved by default and outside users have no right to copy, modify or run it; this is the first thing a forker, packager or contributor checks and cannot be fixed retroactively for early clones, so P0 and blocks_public=true are correct. Fix is as recommended: add a LICENSE file at the root plus `license = "MIT"` (or chosen SPDX id) and `authors` in pyproject.toml.

### From the tests lens: No LICENSE file

Evidence: `git ls-files` has no LICENSE*; `ls LICENSE* CONTRIBUTING*` reports no such file. pyproject.toml [project] has no `license` field and no license classifier. The audit ticket .tickets/kno-01m2ebf5sxdb already lists this as known; recorded here because a public repo with no license grants outsiders no right to use or contribute.

Recommendation: Add a LICENSE file and the matching `license` field / classifier in pyproject.toml before the visibility flip.

Verifier (P0, blocks public: yes): Reproduced at fcc6b66: `git ls-files` matches no LICENSE*/LICENCE*/COPYING*/CONTRIBUTING*, `ls` on those globs finds nothing in the working tree, and `git log --all` shows no such file ever existed in history. pyproject.toml [project] has no `license` field and its classifiers list (Alpha, Web Environment, Developers, Python 3.12, Bug Tracking) contains no `License ::` entry; a repo-wide grep for license/copyright/SPDX outside .tickets returns zero hits in source, README, docs or nix files, so there is no per-file notice standing in for a LICENSE file either. The only mention is the audit ticket .tickets/kno-01m2ebf5sxdb line 19 acknowledging "there is no LICENSE, no CONTRIBUTING and no CI". Severity P0 is correct: without a license, default copyright applies and outsiders have no right to use, modify or redistribute the code, which defeats the purpose of going public and exposes any early adopter; it is not merely something a first contributor hits, it is a precondition for the repo being usable at all. Missing CONTRIBUTING is separate polish (P2) and should not be bundled into this finding.

## Notes

**2026-09-13T23:33:19.953259Z**

Task completed: MIT LICENSE added (assumed to match knot upstream; change the text before publishing if another licence is wanted), pyproject declares license = "MIT" with license-files and the OSI classifier, README has a Licence section; the wheel carries the LICENSE and License metadata.
