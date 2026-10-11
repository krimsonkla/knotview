---
id: kno-01m4mtc60xh9
title: Switch the panel between a repository's git worktrees
status: closed
type: task
priority: 2
mode: afk
created: '2026-10-11T06:28:33.437078Z'
updated: '2026-10-11T07:29:50.940779Z'
closed: '2026-10-11T07:29:50.940779Z'
assignee: Jason Risch
---

## Description

knot keeps `.tickets/` inside the git checkout, so each worktree of a repository holds its own copy of the backlog, and the copies drift as branches move tickets. The panel reads only the directory it was started in, so seeing what a feature worktree's backlog says means starting a second panel on another port.

## Design

- The header offers the repository's worktrees, from `git worktree list --porcelain -z`, only when there is more than one. Choosing one reloads the same page over that worktree's backlog.
- The choice lives in a `knotview_worktree` cookie holding the worktree's path, set by `GET /worktree` and redirected back, as `/tags` does. A path not in the current listing falls back to the launch repository.
- One `KnotCommand` per worktree, cached under a lock. `/digest` folds in the chosen path so other tabs reload after a switch.
- The process guard admits exactly `reading/knot_command.py` and `reading/git_worktrees.py`; the git argv is pinned to that one verb.
- With one worktree, no git repository, or no git binary, the panel looks and behaves as before.

## Notes

**2026-10-11T06:34:33.802661Z**

Starting work on this task.

**2026-10-11T07:29:50.302854Z**

Task completed: the panel lists the repository's git worktrees and reads whichever one the reader picks, in ab30493, 31fbe5e, 96b7c79, 626a6a9 and 594fadf. 456 tests pass at 100 percent line and branch coverage.

Checked by hand against a real panel with a second worktree: the picker marks the current worktree; choosing the other one switches every page and moves the digest; an unlisted path clears the choice; a back link of /\elsewhere returns to /.

Not checked by hand: a second open tab reloading by itself in a real browser after a switch. The server side and the follow.js text are covered by tests (AC-8, AC-21).
