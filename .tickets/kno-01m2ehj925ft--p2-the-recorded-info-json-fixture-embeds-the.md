---
id: kno-01m2ehj925ft
title: '[P2] The recorded info.json fixture embeds the author''s machine path, username and a Claude session id'
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:45.732880Z'
updated: '2026-09-13T23:27:45.862563Z'
assignee: ''
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the docs, hygiene, legal, security lenses and confirmed by an adversarial verifier.

### From the docs lens: Recorded test fixture contains the author's machine path and a Claude session id

Evidence: tests/reading/envelopes/info.json lines 12-17: `"cwd": "/private/tmp/claude-501/-Users-krimsonkla-git-krimsonkla-knotview/d0ad9ed2-6e54-486b-9b6b-5e82fd325168/scratchpad/probe"` and the same prefix for project_root, config_path, tickets_path, archive_path. Functionally harmless (tests/reading/conftest.py rewrites `paths` per test), but it publishes a local username, a scratchpad layout and a session identifier.

Recommendation: Replace the five path values with a neutral placeholder such as `/tmp/example-project/...` and re-run the suite (conftest overrides them so nothing else should change).

Verifier (P2, blocks public: no): Confirmed: /Users/krimsonkla/git/krimsonkla/knotview/tests/reading/envelopes/info.json lines 12-17 contain the literal scratchpad path `/private/tmp/claude-501/-Users-krimsonkla-git-krimsonkla-knotview/d0ad9ed2-6e54-486b-9b6b-5e82fd325168/scratchpad/probe` in cwd, project_root, config_path, tickets_path and archive_path (tracked in git since cfab810). tests/reading/conftest.py lines 37-46 fully overwrite `held["data"]["paths"]` from KNOTVIEW_FAKE_TICKETS before the fake knot emits the envelope, so the values are dead data and replacing them cannot change test behaviour. A grep across the repo (excluding .git/.tickets) found the session id and the `claude-501` prefix nowhere else; `krimsonkla` also appears in devenv.yaml/devenv.lock but only as the public GitHub owner of flake inputs, which is not a leak. Line 21 of the same fixture also holds the author's display name ("Jason Risch"), which matches the public git author so it adds nothing new. Severity P2 is right: it is a cosmetic hygiene issue with no functional or security impact (the session id is not a credential, and the path reveals only a local username and a temp layout), so it does not block going public, though the five path values should be replaced with a neutral placeholder as recommended.

### From the hygiene lens: Recorded fixture carries the author's scratch paths, a Claude session id and the author's name

Evidence: tests/reading/envelopes/info.json:12-17 five path values all equal `/private/tmp/claude-501/-Users-krimsonkla-git-krimsonkla-knotview/d0ad9ed2-6e54-486b-9b6b-5e82fd325168/scratchpad/probe...` (username, machine layout and session UUID); line 21 `"effective_create_assignee": "Jason Risch"`. These are inert at test time: tests/reading/conftest.py:37-48 rewrites `data.paths` per test, and tests/reading/test_real_knot.py:133-139 `shape()` compares key sets only, so replacing the values cannot break a test. `git grep "/Users/"` over tracked files is otherwise clean, and `.idea` appears only in .gitignore:18.

Recommendation: Rewrite the five path values to a neutral placeholder such as `/tmp/probe/...` and `effective_create_assignee` to `null` or a fixture name (knot reports the git user, so a neutral value is faithful to the shape). Re-run `pytest` to confirm the shape test still passes.

Verifier (P2, blocks public: no): The evidence is accurate: `tests/reading/envelopes/info.json` is tracked, lines 12-17 hold five `/private/tmp/claude-501/-Users-krimsonkla-git-krimsonkla-knotview/d0ad9ed2-.../scratchpad/probe...` paths and line 21 holds `"effective_create_assignee": "Jason Risch"`; `git grep` over tracked files (excluding `.tickets`) finds no other `/Users/`, `/private/tmp`, `claude-501`, session-UUID or name hits. I also confirmed the values are inert: `tests/reading/conftest.py:37-48` overwrites `data.paths` wholesale, and `shape()` in `test_real_knot.py:133-139` reduces leaves to type names. But nothing here is secret or blocking: the username `krimsonkla` is the public GitHub org in the repo URL, `Jason Risch` is already the author on every commit, and a Claude scratchpad session UUID is not a credential or an access path. An outside contributor only sees it if they open a recorded fixture, so this is cosmetic hygiene (P2), not P1, and does not block going public. One caveat on the recommendation: `shape()` compares type names, so changing `effective_create_assignee` to `null` would turn `str` into `NoneType` and could fail the live-knot shape comparison; use a neutral string (e.g. `"Fixture Author"`) rather than `null`.

### From the legal lens: Committed fixture embeds the author's machine path, macOS username and a Claude Code session id

Evidence: /Users/krimsonkla/git/krimsonkla/knotview/tests/reading/envelopes/info.json:12-17 contain `/private/tmp/claude-501/-Users-krimsonkla-git-krimsonkla-knotview/d0ad9ed2-6e54-486b-9b6b-5e82fd325168/scratchpad/probe` (cwd, project_root, config_path, tickets_path, archive_path) and line 21 `"effective_create_assignee": "Jason Risch"`. `git log -S'/private/tmp/claude-501'` shows it entered at commit cfab810 (2026-09-13), so it is in history as well as the tree. It is not load-bearing: /Users/krimsonkla/git/krimsonkla/knotview/tests/reading/conftest.py:41-47 overwrites `data.paths` with the test's own root before the fake knot answers.

Recommendation: Replace the five path values with a neutral placeholder such as `/probe` (and the assignee with a placeholder), then rewrite the 18-commit history before the first push so the session id and path never appear publicly; only 18 commits exist and nothing has been pushed, so a rebase is cheap now and impossible later.

Verifier (P2, blocks public: no): The evidence reproduces exactly: tests/reading/envelopes/info.json lines 12-17 hold the /private/tmp/claude-501/-Users-krimsonkla-git-krimsonkla-knotview/d0ad9ed2-.../scratchpad/probe paths and line 21 holds "effective_create_assignee": "Jason Risch"; `git log -S'/private/tmp/claude-501'` pins it to cfab810, and the repo has 18 commits with no remote configured, so it is in history but unpushed. I also confirmed it is not load-bearing: tests/reading/conftest.py lines 41-48 replace data.paths wholesale with the tmp_path root before the fake knot prints, so the fixture values are never observed by any test. The severity is overstated, though. Nothing here is a credential or secret: the author's real name is already the git committer identity on every commit and the assignee on the committed .tickets files, the "krimsonkla" handle is already public in devenv.yaml/devenv.lock as the GitHub owner of the flake inputs, uid 501 is the default macOS first-user id, and a Claude Code session UUID plus a scratchpad path is a hygiene leak with no exploit path. An outside user or contributor does not "hit" this at all; it only surfaces to someone reading a recorded fixture, and the tests behave identically. It is worth a two-minute cleanup (placeholder paths and assignee in the fixture, optionally amend into history since nothing is pushed), but it is polish, not a public-release blocker, and the history rewrite is a cheap nice-to-have rather than a requirement.

### From the security lens: Recorded fixture embeds the author's local scratchpad path and Claude session id

Evidence: /Users/krimsonkla/git/krimsonkla/knotview/tests/reading/envelopes/info.json lines 12-17 contain `/private/tmp/claude-501/-Users-krimsonkla-git-krimsonkla-knotview/d0ad9ed2-6e54-486b-9b6b-5e82fd325168/scratchpad/probe` in cwd, project_root, config_path, tickets_path and archive_path. Not a secret, but it leaks a machine path, the username and an AI session identifier into a public fixture, and the values are irrelevant to what the fixture asserts.

Recommendation: Re-record or hand-edit info.json to use a neutral path such as `/tmp/probe`, and keep the shape-only comparison in test_real_knot.py (which already drops values).

Verifier (P2, blocks public: no): Reproduced: /Users/krimsonkla/git/krimsonkla/knotview/tests/reading/envelopes/info.json lines 12-17 embed `/private/tmp/claude-501/-Users-krimsonkla-git-krimsonkla-knotview/d0ad9ed2-6e54-486b-9b6b-5e82fd325168/scratchpad/probe` (username, machine layout, and a Claude session UUID) in cwd/project_root/config_path/tickets_path/archive_path; the file is tracked (commit cfab810) and is the only file outside .git matching that path. Line 21 also carries the author's name as effective_create_assignee, which the report did not mention but is the same class of leak (the name is already the public git author, so it adds little). Nothing asserts on these values: test_knot_envelope.py only checks `tickets_path.endswith("/.tickets")`, and test_real_knot.py compares via shape(), which drops values, so rewriting the paths to `/tmp/probe` is safe and breaks no test. No secret or credential is exposed, so P2/polish is the right severity and it does not block going public.
