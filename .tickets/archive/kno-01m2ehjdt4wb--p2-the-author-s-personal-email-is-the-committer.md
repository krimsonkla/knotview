---
id: kno-01m2ehjdt4wb
title: '[P2] The author''s personal email is the committer identity on every commit'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:50.596187Z'
updated: '2026-09-13T23:45:45.259771Z'
closed: '2026-09-13T23:45:45.259771Z'
assignee: Jason Risch
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the legal lens and confirmed by an adversarial verifier.

### From the legal lens: Author's personal email is the committer identity on all 18 commits

Evidence: `git log --format='%an <%ae>' | sort -u` → `Jason Risch <jasonrisch@gmail.com>` (single author, every commit). No other email, hostname or third-party name appears in tracked files or history (`git grep -i -E 'gmail|\.internal|@[a-z0-9.-]+\.(com|net|org|io)'` over tracked files excluding lock files returns nothing).

Recommendation: Ordinary for GitHub and not a blocker; if the author prefers the address not to be public, set `user.email` to the GitHub noreply address and rewrite the 18 commits before the first push, alongside the fixture-path rewrite above.

Verifier (P2, blocks public: no): Reproduced: `git log --format='%an <%ae> | %cn <%ce>' | sort | uniq -c` shows all 18 commits (`git rev-list --count HEAD` = 18) with both author and committer set to `Jason Risch <jasonrisch@gmail.com>`; no other identity appears, and no commit bodies contain an `@` trailer. `git remote -v` prints nothing, so the history has not been pushed and a pre-push rewrite (or simply leaving it) is still possible. One small correction to the reviewer's evidence: the tracked-file grep is not empty — `devenv.yaml:3` contains `git+ssh://git@github.com/krimsonkla/devenv-layers`, which matches the pattern but is a normal SSH remote URL, not a personal email, so it does not change the finding. The finding is factually accurate but describes the ordinary state of any GitHub repo authored by one person; a personal email in commit metadata is not a security, legal or first-user problem, so P2 (author's-preference polish) is the correct severity and it does not block going public.

## Notes

**2026-09-13T23:45:45.259771Z**

The committer identity is the author's own choice and the same address is on the author's public GitHub profile; rewriting 30 commits to change it is not the panel's business.
