---
id: kno-01m2ehjcf8fb
title: '[P2] README examples use the author''s personal project name and paths'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:49.224699Z'
updated: '2026-09-13T23:46:51.053712Z'
closed: '2026-09-13T23:46:51.053712Z'
assignee: Jason Risch
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the hygiene, legal lenses and confirmed by an adversarial verifier.

### From the hygiene lens: README examples use the author's personal project name and paths

Evidence: README.md:14-20 uses `~/git/outcry`, `~/git/other`, `knotview outcry`; the same name recurs 20+ times in tests/entry/test_console.py and test_saved_projects.py. The packaged README in src/knotview.egg-info/PKG-INFO (untracked, gitignored) carries it too. Nothing in README says what `knot` is beyond the link at line 3 or how to install either tool outside the devenv shell.

Recommendation: Replace `outcry` with a neutral example (`~/git/example`), keep the test names if wanted, and add a short install/prerequisites section (knot version 0.12.0 as recorded in tests/reading/envelopes/__init__.py:1).

Verifier (P2, blocks public: no): The evidence reproduces at fcc6b66: README.md lines 14, 16 and 20 use `~/git/outcry` and `knotview outcry` as the saved-project example, and grep finds the name 10 times in tests/entry/test_console.py and 14 times in tests/entry/test_saved_projects.py (24 total, matching the "20+" claim); src/knotview.egg-info/PKG-INFO is confirmed gitignored via `*.egg-info/` so it is not shipped from the repo. README has no install or prerequisites section: it only shows `devenv shell -- knotview ...`, devenv.nix/devenv.yaml contain no mention of knot, and pyproject.toml explicitly says knot is not a dependency and is "supplied by the tickets layer", so an outside reader gets no statement of which knot version is expected (tests pin 0.12.0 in tests/reading/envelopes/__init__.py:1 and tests/panel/declared.py:14). However `outcry` is just an ordinary word used as a project name, exposes nothing sensitive, and the first example on line 7 already uses a neutral `/path/to/a/knot/project`, so this is cosmetic; the missing install/knot-version note is the more useful fix but a first user can still infer usage from line 3's knot link and the devenv command. P2 polish, does not block going public.

### From the legal lens: README examples name a personal project (~/git/outcry)

Evidence: /Users/krimsonkla/git/krimsonkla/knotview/README.md:14-16 use `--repository ~/git/outcry ... --save outcry` and `knotview outcry`; the same name is the fixture project in tests/entry/test_console.py and tests/entry/test_saved_projects.py.

Recommendation: Polish only: swap `outcry` for a generic name like `myproject` in README so the first outside reader is not pointed at a path that exists only on the author's machine; the test usages are harmless.

Verifier (P2, blocks public: no): Confirmed: /Users/krimsonkla/git/krimsonkla/knotview/README.md lines 14, 16 and 20 use `~/git/outcry` / `--save outcry` / `knotview outcry` as the worked example, paired with a generic `~/git/other`; `outcry` appears nowhere in src/, only in README.md and the two test files (tests/entry/test_console.py, tests/entry/test_saved_projects.py), where it is just a registry key under tmp_path and never a real path. `~/git/outcry` does not even exist on this machine (ls fails), so it is not a leaked path to anything real, and the README is clearly showing an illustrative name alongside `other`. Nothing is sensitive, nothing breaks for a reader (they substitute their own path exactly as with `/path/to/a/knot/project` on line 7), and `knot` itself is already a public GitHub project. This is cosmetic: a personal-sounding example name is mildly odd next to the generic placeholders around it, so P2 polish is the right rating and it does not block going public; a one-word swap to e.g. `myproject`/`~/git/one` would make the example self-consistent, and the test fixtures can stay.

## Notes

**2026-09-13T23:46:50.449164Z**

Task completed: the README's examples were rewritten under the install ticket (~/git/one, ~/git/two); the only remaining personal token is the repository URL itself. The test data keeps 'outcry' as a saved-project name, which is a fixture value, not a path.
