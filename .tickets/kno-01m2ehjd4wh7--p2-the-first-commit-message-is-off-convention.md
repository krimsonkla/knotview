---
id: kno-01m2ehjd4wh7
title: '[P2] The first commit message is off-convention'
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:49.916698Z'
updated: '2026-09-13T23:27:50.037864Z'
assignee: ''
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the hygiene lens and confirmed by an adversarial verifier.

### From the hygiene lens: First commit message is off-convention and the working tree is dirty

Evidence: `git log --oneline`: 17 of 18 commits use conventional prefixes (feat/fix/test/refactor/chore/docs with scopes); the root commit d42c924 is bare "initial implementation" with no body, and .tickets/archive/kno-01m2ebf3w4q3...md:15 records it was made with --no-verify. All commits are by the author's personal gmail address (fine, but it will be public). `git status` shows .tickets/kno-01m2ebf5sxdb...md modified and uncommitted (status open -> in_progress, assignee set, a note appended). No secrets found in any commit's tracked content.

Recommendation: Optional: reword the root commit to `feat: initial implementation of the read-only knot panel` before the first push (history is unpublished, so a rewrite is cheap now and impossible later); commit or revert the ticket transition so main is clean at the moment it goes public.

Verifier (P2, blocks public: no): Reproduced every claim. `git log` shows 18 commits, all authored by the personal gmail address; 17 carry conventional type(scope) subjects and the root commit d42c924 is the bare subject "initial implementation" with no body. `.tickets/archive/kno-01m2ebf3w4q3--lint-panel-complexity-and-the-three-value-objects.md:15` records that the initial commit was made with --no-verify because of four lint findings. `git status --short` shows exactly one modified file, `.tickets/kno-01m2ebf5sxdb--audit-what-must-be-completed-before-the.md`, and `git diff` confirms it is the audit ticket's own open -> in_progress transition (assignee set, one timestamped note appended) — which is the expected state while this audit is running, not a stray change. No remote is configured and no remote branches exist, so history is indeed unpushed and a reword of the root commit is still cheap. This is real but purely cosmetic: a plain root commit subject and an in-flight ticket edit are things nobody outside the project hits, and the dirty file is a ticket, not code, so P2 and non-blocking is the correct call.
