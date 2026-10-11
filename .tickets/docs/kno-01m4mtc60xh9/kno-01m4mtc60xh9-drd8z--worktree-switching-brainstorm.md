---
id: kno-01m4mtc60xh9-drd8z
ticket: kno-01m4mtc60xh9
title: Worktree switching brainstorm
type: other
created: '2026-10-11T06:28:52.605636Z'
updated: '2026-10-11T06:28:52.605636Z'
---

# Worktree switching brainstorm

Ticket: kno-01m4mtc60xh9. Date: 2026-10-10.

## Problem

knot keeps `.tickets/` inside the git checkout. Each worktree of a repository therefore holds its
own copy of the backlog, and the copies drift as branches move tickets. The panel reads only the
directory it was started in. To see a feature worktree's backlog today, you start a second panel on
another port.

## Decisions

| Question | Choice | Rejected |
| --- | --- | --- |
| What problem to solve | Switch between worktrees, one backlog at a time | Drift badges across worktrees; one merged view; CLI-only convenience |
| Where the choice lives | A cookie, as `tags.py` does | The URL (every route, link builder and the digest would carry it); one panel per worktree |
| How worktrees are found | `git worktree list --porcelain -z` | Reading `.git/worktrees/*/gitdir` (a second parser of git internals) |

## Design

### What the reader sees

The header offers a worktree picker only when the repository has more than one worktree. Each entry
shows the branch, or the short head when detached, and the directory name. The current entry is
marked. Choosing an entry reloads the same page over that worktree's backlog. With one worktree, no
git repository, or no git binary, the panel looks and behaves as before.

### Units

1. `reading/git_worktrees.py`: `GitWorktrees(repository, git="git").listed()` runs exactly
   `git -C <repo> worktree list --porcelain -z` and returns `Worktree` values (path, branch or
   None, head, main or not). It drops bare and prunable entries. When git fails, or the directory
   is not a repository, it returns the launch repository alone, so the feature switches itself off.
2. `values/worktree.py`: a frozen dataclass.
3. `panel/worktree_choice.py`: mirrors `tags.py`. The `knotview_worktree` cookie holds the
   worktree's path, because branch names can collide or be absent. `GET /worktree?path=…&back=…`
   sets it and redirects back, through the same this-panel-only redirect guard as `/tags`.
4. The backlog is chosen per request. `Pages` no longer holds one `backlog`; a resolver maps the
   cookie to a `Backlog`.
   - It accepts only a path in the current `git worktree list`. Any other cookie value falls back
     to the launch repository, so an edited cookie cannot point knot at an arbitrary directory.
   - It caches one `KnotCommand` per worktree path under a lock, because page handlers run in the
     thread pool.
   - `panel(backlog)` still works for tests: the worktree source and backlog factory are optional
     arguments that default to one worktree.
5. `/digest` folds in the chosen worktree's path. The cookie is shared by every tab, so a switch in
   one tab makes the others reload on their next poll.
6. `test_only_the_command_module_reaches_outside_the_process` admits exactly
   `{reading/knot_command.py, reading/git_worktrees.py}`. A new test pins the git argv to the one
   read-only verb.

### Edge cases, handled by existing behaviour

- A ticket page for an id the other worktree lacks shows the existing not-found refusal.
- A worktree whose backlog cannot be read shows the existing unreadable-backlog page. The picker
  stays on that page so the reader can switch back.
- Chosen tags the other worktree does not use narrow the lists to nothing, as today.

### Out of scope

- The CLI and saved projects do not change. A panel started in any worktree already sees all its
  siblings, because git lists every worktree from any one of them.
- Comparing tickets across worktrees.

## Acceptance criteria (proposed)

- A repository with two or more worktrees shows a picker naming each by branch (or short head) and
  directory, with the current one marked.
- Choosing a worktree reloads the same page over that worktree's backlog.
- A cookie naming a path outside git's current worktree listing reads the launch repository.
- With one worktree, no git repository, or no git binary, the panel looks and behaves as before.
- Only `knot_command.py` and `git_worktrees.py` may start a process, and git is only asked to list
  worktrees.

## Size

Two small modules, one value, a mechanical `self.backlog` to `self._backlog(request)` change at
about 15 call sites in `app.py`, one template partial, and CLAUDE.md updates.
