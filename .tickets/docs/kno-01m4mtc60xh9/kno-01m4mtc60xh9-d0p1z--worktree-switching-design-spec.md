---
id: kno-01m4mtc60xh9-d0p1z
ticket: kno-01m4mtc60xh9
title: Worktree switching design spec
type: spec
created: '2026-10-11T07:29:23.451002Z'
updated: '2026-10-11T07:29:23.451002Z'
---

# Worktree Switching Design Spec

## Changes Since Last Cycle

Plan gate (findings 230-233 and the voters' notes):
- R9: the digest wording now matches the scheme. The launch directory's digest is the backlog's
  own, and any other worktree's is prefixed with a digest of its path (233).
- R15: a panel launched in a subdirectory reads the same subdirectory of a chosen worktree
  (consumer-integration-engineer). AC-15 is extended.
- R5 and AC-6: a way back containing a backslash is refused (security-engineer).
- R3: git output that cannot be decoded, and paths that cannot be resolved, are skipped rather
  than raised (backend-eng).
- Risks: cross-site GET on `/worktree`, trust in each branch's `.knot.edn`, and a reader cache
  that is never evicted are recorded as accepted.

**Story:** Switch the panel between a repository's git worktrees (kno-01m4mtc60xh9)
**Tier:** System. It spans the reading layer (a new process), the panel's request handling, the
shared page frame and the digest poll.
**Brainstorm:** `.tickets/docs/kno-01m4mtc60xh9/kno-01m4mtc60xh9-drd8z--worktree-switching-brainstorm.md`

## Problem

knot keeps `.tickets/` inside the git checkout. Each worktree of a repository therefore holds its
own copy of the backlog, and the copies drift as branches start, move and close tickets. The panel
reads only the directory it was started in. To see what a feature worktree's backlog says, a reader
starts a second panel on another port and keeps track of which tab is which.

## Goal

From one panel, a reader can read any worktree of the repository's backlog, one at a time, without
restarting anything.

**Success signals:** in a repository with two worktrees whose backlogs differ, choosing the other
worktree changes what every page shows to that worktree's tickets, and choosing back restores them.

## Scope

**In scope:** finding the repository's worktrees; a picker in the page frame; remembering the
reader's choice; reading every page, and the digest, over the chosen worktree.

**Out of scope:**
- Comparing or merging tickets across worktrees (rejected at brainstorm).
- Changes to the `knotview` command or to saved projects. A panel started in any worktree already
  sees all of its siblings, because git lists every worktree from any one of them.
- Creating, removing or pruning worktrees.
- Making the unreadable-backlog page poll the digest. It does not poll today.

**Non-goals:**
- Showing two worktrees at once in two tabs of one panel. The choice is one per browser, like tags.
- Any write to a worktree, to git, or to a backlog.

## Requirements

| ID | Priority | Requirement |
|----|----------|-------------|
| R1 | MUST | The panel lists the repository's worktrees by asking git, never by reading git's internal files. |
| R2 | MUST | Bare and prunable worktrees are not offered. |
| R3 | MUST | The supported git is 2.36 or later (the first with `worktree list -z`). When git cannot answer (no git binary, not a repository, an older git that rejects an option, a non-zero exit, output that does not parse, or no answer within the patience knot reads get), the only worktree is the launch repository, and nothing is shown or refused because of it. A single worktree whose path cannot be decoded as UTF-8 or cannot be resolved (a symlink loop) is left out, and the rest are offered. |
| R4 | MUST | The page frame shows a picker only when more than one worktree is offered. Each entry's text is `<name> · <directory name>`, where name is the branch without `refs/heads/`, or the first 7 characters of the head when detached. Each entry carries its full path as its `title`. The entry being read carries `aria-current="true"`, and no other entry does. |
| R5 | MUST | Choosing a worktree is a GET that stores the choice in a cookie in the reader's browser and redirects back to the page the reader was on. The redirect target obeys the same rule as `/tags`: a path on this panel, else `/`. A target that does not start with one `/`, or that contains a backslash, is refused, since browsers read `/\` as `//`. |
| R6 | MUST | The cookie holds the worktree's path. A cookie whose path is not among the worktrees git currently lists reads the launch repository, so a cookie can never point knot at an arbitrary directory. |
| R7 | MUST | Every page, every refusal page and the digest read the chosen worktree's backlog. |
| R8 | MUST | A worktree's backlog reader is created once and reused. Both the reader cache and the shared most-recent worktree list are safe when several request threads read and write them at once. A list is replaced whole, and a reader never sees part of an update. |
| R9 | MUST | Each page that polls carries the digest it was rendered under, read before the page reads its data. The poll compares each answer against that value, so the page reloads whenever the chosen worktree or its backlog differs from what it shows, including after a switch made in another tab. The digest is the backlog's own digest when the launch directory is read, and for any other worktree that digest prefixed with a short digest of the worktree's path, so the value differs whenever the chosen worktree does. If reading the digest for a render is refused, the page still renders, carries no digest, and the poll takes its baseline from its first answer, as it does today. |
| R10 | MUST | The digest poll starts no git process. It checks the cookie against the worktree list from the most recent page render. Before any page has rendered (a restarted panel with a tab still open), the poll reads the launch repository. |
| R11 | MUST | Only the knot reader module and the new git module may start a process. The git module's argv is exactly `git -C <resolved launch repository> worktree list --porcelain -z`, with `git` replaced by the configured git command. |
| R12 | MUST | With one worktree, no repository or no git, every page renders as it does today: no picker, and no added text. The carried digest (R9) is the one allowed difference, and it is not visible. |
| R13 | SHOULD | The cookie is named `knotview_worktree_` plus a short digest of the resolved launch repository path, so panels over different repositories on one host do not overwrite each other's choice. |
| R14 | SHOULD | The unreadable-backlog page shows the picker, with the current path to come back to, whenever more than one worktree is offered. This includes the case where the launch repository's own backlog cannot be read, because git's list does not depend on knot. |
| R15 | MUST | The launch repository, each path git lists and the cookie's path are resolved to their real paths before any comparison, so a symlinked launch directory matches git's entry for it. When the resolved launch directory is inside a listed worktree rather than equal to one, the deepest listed worktree that contains it is the one marked when no other is chosen. When none contains it, no entry is marked. In both cases the fallback still reads the launch directory itself. When the launch directory is a subdirectory of a listed worktree, choosing another worktree reads the same relative subdirectory inside it, so a knot project kept below a repository's root is found in every worktree. |
| R16 | MUST | The cookie value survives any path, including paths with spaces, commas, semicolons, quotes and non-ASCII characters. It is encoded when set and decoded when read. |

## Design

**Approach:** A git reader lists worktrees. A resolver turns each request's cookie into one of
those worktrees, or the launch repository, and hands back that worktree's `Backlog`. `Pages` asks
the resolver for the backlog on every request instead of holding one. A `/worktree` route, which
mirrors `/tags`, sets the cookie. The page frame renders the picker from the resolver's list.

**Components and responsibilities:**
- **Worktree value**: resolved path, branch (or none), head, and whether it is the main worktree.
  It is frozen, like the other values.
- **Git worktree reader** (reading layer): runs the one listing command and parses porcelain `-z`
  output into worktree values. Any failure yields the launch repository alone (R3). It is the second
  and last module allowed to start a process.
- **Worktree choice** (panel layer): the cookie's name, encoding and decoding a path in a cookie,
  and matching it against a list of worktrees. It mirrors `tags.py`.
- **Backlog resolver** (panel layer): holds the launch repository, the git reader, a factory from
  a path to a `Backlog`, the most recent listing (none until the first page render), and a per-path
  cache of backlogs, all behind a lock. It answers "the worktrees offered", "the worktree this
  request reads" and "the backlog for this request". Page renders refresh the listing. The digest
  only reads it.
- **Pages**: unchanged pages, which now ask the resolver for their backlog. Add one `worktree`
  handler. Pass the picker's entries and the rendered digest to the frame. The unreadable page also
  receives the picker's entries and the current path.
- **Page frame** (`layout.html`, and the bare frame the unreadable page uses): the picker. The
  layout also carries the rendered digest for `follow.js`.
- **Follow script** (`follow.js`): takes its baseline from the digest the page carries, rather than
  from the first answer.

**Interfaces and contracts:**
- `panel(backlog)` keeps its current signature and behaviour for every existing test. The
  resolver's git reader and backlog factory are optional keyword arguments, and their defaults
  mean "exactly one worktree, this backlog".
- The command line builds the panel with a git reader over the launch repository and a factory
  that makes a `KnotCommand` with the same knot command and patience.
- `GET /worktree?path=<path>&back=<path on this panel>` returns a 303 to `back`. A `path` that
  resolves to one of the current worktrees sets the cookie (`SameSite=Strict`, `HttpOnly`, as tags
  do). Any other `path`, or none, deletes the cookie. The route lists worktrees but never starts
  knot.
- `/digest` reads the request's cookie to choose its backlog, and stays a plain-text answer.

**Data and state:** one new cookie in the reader's browser. In memory: the last worktree listing
and one backlog reader per worktree path, for the life of the process. Nothing is written to disk.
The since-last-looked marks in `follow.js` stay one stored instant per browser. They compare each
row's own `updated` time to that instant, so they stay correct when the worktree changes.

**Prior art to mirror:**
- `src/knotview/panel/tags.py` and `Pages.tags`: the cookie value, a GET that sets it, and the
  this-panel-only redirect check. Lift the redirect check into one shared helper rather than
  copying it.
- `KnotCommand._located`: the lock-guarded first computation of a remembered value. `KnotCommand`
  remembers only where its project's directories are, and the resolver's cache follows the same
  locking.
- `KnotCommand._read` and `_spoken`: a pinned argv and a timeout. The git reader copies both. It
  does not refuse, because of R3.
- `tests/reading/conftest.py`: the fake executable pattern for driving the git reader in tests.

**Key decisions:**
- Switch one worktree at a time. This is the problem the reader asked to solve.
- The choice lives in a cookie, not the URL. Every route, link and the poll would otherwise carry
  it.
- Discovery uses git's porcelain output. That is git's stable contract, as `--json` is knot's.
- The cookie holds a path, not a branch name. Branches can be absent (detached) or renamed.
- The cookie is checked against the live list before use. This makes it safe to use the cookie to
  choose a directory to run knot in.
- One reader per worktree, cached under a lock, because handlers run in the thread pool.
- The digest folds in the chosen path, and the page carries the digest it rendered under, because
  a cookie is shared by every tab.

**Alternatives rejected:**
- Drift badges, or one merged view across worktrees: a different problem from the one chosen.
- The worktree in the URL: much wider change for per-tab independence the reader did not ask for.
- One panel per worktree: no switching from one panel.
- Reading `.git/worktrees/*/gitdir` directly: a second parser of a format git owns.
- Since-last-looked marks per worktree: the marks compare times, so one instant is already correct.

## Acceptance Criteria

### Story 1: When a repository has several worktrees, I want to choose which one the panel reads, so I can see a branch's backlog without starting another panel.

**AC-1**: picker lists the worktrees
Given a repository with a main worktree on `main` and a second worktree on `feature`
When the reader opens any page
Then the frame lists `main · <dir>` and `feature · <dir>`, and only the main entry has `aria-current="true"`.

**AC-2**: choosing switches every page
Given the picker from AC-1
When the reader chooses the `feature` worktree
Then they are redirected back to the same page, and it shows the `feature` worktree's tickets.

**AC-3**: the choice persists
Given the reader has chosen the `feature` worktree
When they open a different page
Then that page also reads the `feature` worktree, and only the `feature` entry has `aria-current="true"`.

**AC-4**: detached worktree
Given a worktree whose HEAD is detached
When the picker renders
Then that entry's text is the first 7 characters of its head, then ` · `, then its directory name.

**AC-5**: a path git does not list (negative)
Given a cookie that names a directory not in git's current worktree list
When the reader opens any page
Then the page reads the launch repository, and no backlog reader is made for that directory.

**AC-6**: unsafe way back (negative)
Given a request to choose a worktree with `back` set to `//elsewhere.example`, `/\elsewhere.example` or `https://elsewhere.example`
When it is answered
Then it redirects to `/`.

**AC-7**: a broken worktree (negative)
Given the reader chose a worktree whose backlog cannot be read
When they open a page
Then the unreadable-backlog page shows the picker, and its links lead back to that page's path.

**AC-14**: a ticket the other worktree lacks (negative)
Given the reader is on the page of a ticket that exists only in the main worktree
When they choose the `feature` worktree
Then they are redirected back to that page, and it answers with the existing not-found page and the picker.

**AC-15**: a symlinked launch directory
Given the panel was started through a symlink to the main worktree
When any page renders
Then the picker lists each worktree once, and the main entry has `aria-current="true"`.

**AC-22**: a launch directory below a worktree's root
Given the panel was started in `sub/` of the main worktree
When the reader chooses the `feature` worktree
Then the page reads `sub/` of the `feature` worktree.

**AC-16**: hidden worktrees (negative)
Given git lists a bare entry and a prunable entry besides two usable worktrees
When the picker renders
Then it lists only the two usable worktrees.

**AC-17**: awkward paths
Given a worktree whose path contains a space, a comma, a semicolon, a double quote and a non-ASCII character
When the reader chooses it and then opens another page
Then that page reads that worktree.

### Story 2: When another tab or the repository changes, I want open pages to stay true, so I never read one worktree while the picker names another.

**AC-8**: other tabs follow a switch
Given a page rendered over the main worktree, carrying its rendered digest
When the cookie is switched to the `feature` worktree and the digest is next requested
Then the digest differs from the one the page carries.

**AC-9**: the poll starts no git (negative)
Given an open page
When the digest is requested
Then no git process starts.

**AC-10**: a removed worktree (negative)
Given the reader chose a worktree that has since been removed
When they next open a page
Then it reads the launch repository, and the picker no longer lists the removed worktree.

**AC-18**: a restarted panel (negative)
Given a freshly started panel that has rendered no page, and a cookie naming a linked worktree
When the digest is requested
Then no git process starts, and the answer equals the launch repository's digest value.

**AC-21**: the poll starts from what the page shows
Given a page that carries a rendered digest
When its first poll answer differs from that digest
Then the page reloads, instead of adopting the answer as its baseline.

**AC-19**: concurrent first use
Given no reader exists yet for a worktree
When several requests for that worktree arrive at once
Then exactly one backlog reader is made for it.

### Story 3: When there is nothing to switch between, I want the panel unchanged, so the feature costs nothing where it does not apply.

**AC-11**: one worktree
Given a repository with one worktree
When any page renders
Then it has no picker, and apart from the non-visible carried digest it is the same as before this change.

**AC-12**: git cannot answer (negative)
Given that git is missing, the directory is not a repository, git exits non-zero, git rejects `-z`, or git does not answer within the patience
When the panel serves pages
Then it serves the launch repository with no picker and no error.

**AC-13**: process boundary (negative)
Given the package source
When the process-boundary test scans it
Then the set of modules that start processes is exactly the knot reader module and the git module, and the git argv equals the one in R11.

**AC-20**: separate repositories keep separate choices
Given two panels launched over two different repositories
When each sets its choice
Then the two cookies have different names.

### Traceability

| Story AC | Spec ACs | Requirements | Notes |
|----------|----------|--------------|-------|
| A repository with two or more worktrees shows a picker naming each by branch (or short head) and directory, the current one marked | AC-1, AC-4, AC-15, AC-16 | R1, R2, R4, R15 | |
| Choosing a worktree reloads the same page over that worktree's backlog | AC-2, AC-3, AC-8, AC-14, AC-17, AC-19, AC-21, AC-22 | R5, R7, R8, R9, R16 | |
| A cookie naming a path outside git's current worktree listing reads the launch repository | AC-5, AC-10, AC-18 | R6, R10, R15 | |
| With one worktree, no git repository, or no git binary, the panel looks and behaves as before | AC-11, AC-12 | R3, R12 | |
| Only knot_command.py and git_worktrees.py may start a process, and git is only asked to list worktrees | AC-13, AC-9 | R11, R10 | |
| (from brainstorm edge cases) | AC-6, AC-7, AC-14 | R5, R14 | |
| (ticket names the cookie `knotview_worktree`) | AC-20 | R13 | The name gains a repository suffix. |

## Boundaries

- ✅ Always: mirror `tags.py` for the cookie and route. Keep every route a GET. Keep docstrings
  explaining why. Name tests as sentences that assert rendered content. Hold the 100 percent line
  and branch coverage gate.
- ⚠️ Ask first: any change to `panel()`'s required arguments; showing the repository path or other
  new text in the frame when there is one worktree; any new dependency.
- 🚫 Never: read `.git/` files directly; pass any git verb other than the listing; open a directory
  from the cookie without matching it to git's list; start git from the digest poll; weaken the
  process-boundary test beyond adding exactly the one module.

## Testing Strategy

| AC | Level | Notes |
|----|-------|-------|
| AC-1 to AC-4, AC-14, AC-16 | integration (TestClient) | A fake worktree source returns the worktrees. Each worktree maps to its own `DeclaredBacklog` with different tickets, because a declared backlog's digests are a consumed sequence. |
| AC-5, AC-10 | integration | A factory that records the paths it was asked for proves that no backlog was made for the unlisted path. |
| AC-6 | integration | Same cases as the existing `/tags` redirect tests. |
| AC-7 | integration | A backlog that raises `UnreadableBacklog`. Also cover the launch backlog being the unreadable one. |
| AC-8, AC-9, AC-18 | integration | Compare the digest the page carries with the next answer under the switched cookie. A git source that counts its calls stays at zero across digest requests. |
| AC-15 | unit plus real git | A temporary repository reached through a symlink, and a launch directory that is a subdirectory of a worktree. |
| AC-21 | unit (script text) | Like the existing `test_live.py` script assertions: the baseline comes from the carried digest, and a first answer sets it only when the page carries none. |
| Existing seam | integration | `DeclaredBacklog` needs no change. Its default sequence is `["d1"]`, so a second render on one backlog is refused its digest and renders without one (R9). One existing test compares two rendered pages (`test_overview_links.py`) and must ignore the carried digest. |
| AC-17 | integration | The round trip through `/worktree` and the next request. |
| AC-19 | unit | Many threads ask for one path at once, and the factory counts calls. Mirror the existing lock test for `KnotCommand`. |
| AC-11, AC-12 | integration plus unit | The existing suite passes unchanged. A fake `git` script covers a missing binary, a non-zero exit, a rejected option, a timeout and malformed output. |
| AC-13 | unit | Extend the existing source-scan test, and assert argv equality for git. |
| AC-20 | unit | Two launch paths give two cookie names. |
| Porcelain parsing | unit | Main, linked, detached, bare, prunable and locked records, separated by `-z`. |

**Not automatable:** that git's real porcelain matches the fixture. Verify this once against a real
`git worktree add` in a temporary repository, in a test that skips when git is absent (mirror
`test_real_knot.py`).

## Risks and Open Questions

- [P2] Cookies are shared across ports. Two panels over the **same** launch repository share a
  choice under R13. This is acceptable, because they read the same worktrees. Affects R13.
- [P2] A worktree removed while a tab polls it makes that tab's digest fail until the next page
  render. The existing back-off in `follow.js` covers this, and AC-10 covers the next render.
  Affects R10.
- [Risk] `app.py` changes at about 15 call sites. This is mechanical, but every page's tests must
  still pass unchanged, which is itself the check.
- [Accepted, security-engineer] `/worktree` is a GET a page on another site can trigger, as `/tags`
  is. The impact is switching among worktrees git lists. Affects R5.
- [Accepted, security-engineer] knot reads each worktree's own `.knot.edn`, so a checked-out branch
  controls knot's configuration for that worktree. The panel stays read-only. Affects R7.
- [Accepted, devops-sre and solution-architect] The reader cache is never evicted. It is bounded
  by the worktrees ever listed in one process. Affects R8.
- [Risk] A git older than 2.36 makes the feature silently absent (R3). This is acceptable for a
  loopback tool, and AC-12 pins the behaviour.

## Assumptions

1. A list as old as the last page render is current enough for the digest poll. — Impact: MEDIUM
   (confirmed by the developer)
   Correct this if: readers expect a worktree added in a terminal to appear without reloading.
2. Browsers share cookies across ports, so the cookie name carries a digest of the launch
   repository. — Impact: LOW (confirmed by the developer)
   Correct this if: one shared choice across all panels is wanted.
3. "Launch repository" means the directory the panel was started in, even when that is a linked
   worktree rather than the main one. — Impact: MEDIUM (confirmed by the developer)
   Correct this if: the fallback should always be the main worktree.

## Cross-story collision check

No collision found: no pull request is open on krimsonkla/knotview (checked 2026-10-10).

---
After implementing, compare results against each acceptance criterion above
and list any unmet requirements.
