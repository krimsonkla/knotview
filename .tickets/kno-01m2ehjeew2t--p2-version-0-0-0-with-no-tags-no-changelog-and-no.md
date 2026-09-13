---
id: kno-01m2ehjeew2t
title: '[P2] Version 0.0.0 with no tags, no changelog and no project URLs or authors in package metadata'
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:51.259877Z'
updated: '2026-09-13T23:27:51.383880Z'
assignee: ''
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the packaging lens and confirmed by an adversarial verifier.

### From the packaging lens: Version 0.0.0, no tags, no changelog, and no project URLs/authors in package metadata

Evidence: pyproject.toml `version = "0.0.0"` with classifier `Development Status :: 3 - Alpha`; `git tag` prints nothing across 18 commits; no CHANGELOG file tracked; `[project]` has no `authors`, `urls`, or `license` keys (wheel METADATA therefore carries no repository link).

Recommendation: 0.0.0 is tolerable for a first public push but bump to 0.1.0 and tag `v0.1.0` at the publish commit, add `[project.urls] Repository = ...`, `authors`, and a short CHANGELOG.md; consider `dynamic = ["version"]` via setuptools-scm later so tags drive the version.

Verifier (P2, blocks public: no): Reproduced every claim: pyproject.toml has version = "0.0.0" with the "Development Status :: 3 - Alpha" classifier and the [project] table has no authors, urls, or license keys; git tag prints nothing across 18 commits (git rev-list --count HEAD = 18); git ls-files shows no CHANGELOG/HISTORY/release-notes file. The package is still fully installable and runnable (build-system, dependencies, project.scripts, and setuptools package discovery are all present), so the gap is provenance/discoverability metadata rather than anything a first user hits functionally. P2 polish, does not block going public. Adjacent observation outside this finding: no LICENSE file is tracked at all, which belongs to a separate licensing finding.
