# Changelog

All notable changes are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [1.2.0] - unreleased

The ready queue ordered by what each ticket frees, progress by tag, and comparing worktrees.

### Security

- black, a dev-only formatter, is locked at 26.10.1 for a high-severity advisory in 26.10.0.

### Added

- The ready queue is ordered by how many tickets closing each one frees, then by priority. The
  number is knot's leverage: the live tickets that depend on a ticket through deps,
  directly or through other tickets.
- Each ready row says how many tickets it frees, for example "frees 7". A row that frees nothing
  says nothing. The overview's ready list uses the same order and the same note.
- When the overview shows parents, the gear can add a *start here* list naming the ready tickets
  that free the most, up to three. It is hidden until chosen, like the extra charts.
- A chart by tag on the overview, behind the gear. Each tag shows how many of its tickets are
  closed, out of all its tickets. Each row links to the list of the tag's tickets, closed ones
  included. Pinned tags are not shown, because every ticket on the page already has them. After
  eight tags, the rest fold.
- A Compare page, `/compare?with=<worktree>`, that compares the backlog of the worktree you read
  with the backlog of one other worktree. It lists the tickets only one side holds, the tickets
  closed on one side and live on the other, and the tickets whose status, priority, title or type
  differ. It counts the tickets that are the same. The other worktree must be one that git lists,
  and the page reloads when either backlog changes. An icon beside the worktree dropdown opens it.

### Changed

- Sorted by leverage, a row on the tickets list now says "frees N" in place of "leverage N", and
  says nothing when the number is zero. Tickets with the same leverage now sort by priority.

## [1.1.0] - unreleased

Charts over time on the overview.

### Added

- Three charts over time on the overview, behind the gear: open tickets at the end of each week,
  tickets opened and closed each week, and lead time from created to closed. They cover the last
  twelve weeks, or fewer for a younger backlog. They come from each ticket's `created` and
  `closed` times, so the panel still keeps no history. Past status changes are not recorded, so
  there is no chart of time in progress.

### Security

- Pillow, used only to build the README tour, now needs 13.0.0 or later, which fixes several
  high-severity advisories in 12.3.0.
- certifi, which the test client pulls in through httpx, is locked at 2026.10.19 for a critical
  advisory in 2026.7.22.

### Fixed

- A project whose parents state their own acceptance criteria no longer gets a second
  overview card listing the same parents. Each parent's criteria now show in its row on the one
  card.

## [1.0.0] - unreleased

A redesign of every page, and worktree switching. Tag `v1.0.0` at the commit that is published.

### Added

- Every worktree of the repository can be read from one panel, chosen from a dropdown in the
  header and kept in a cookie in your browser.
- A theme switch in the header: System, Light or Dark, kept in your browser.
- Filters on the tickets list apply as you choose them. Each option shows how many tickets it
  leaves, and the rarer filters sit in a More filters dialog that applies on Apply.
- The overview's charts are chosen behind a gear and kept in your browser.
- With no parents, the overview lists what is ready to start, or the open tickets.
- Markdown tables render as tables.
- The README opens with an animated tour of every view, made by
  `scripts/capture_screenshots.py` from a demo backlog.

### Changed

- The look is built on Primer Primitives (MIT), kept in the package, with a teal accent.
- Lists are one row per ticket instead of a table. Every status, type, tag, assignee and priority
  links to the list filtered by it.
- A ticket page leads with its documents and description, folds later sections, and puts related
  tickets behind tabs, with a sidebar of its facts.
- A tickets URL in any other spelling than the panel's own is redirected to it.
- Tags pinned in the header narrow every page; a list's Tag menu narrows that list alone.

### Fixed

- A `back` link of `/\host` on `/tags` and `/worktree` is refused rather than followed off the
  panel.

## [0.1.0] - unreleased

The first version. Tag `v0.1.0` at the commit that is published.

### Added

- The panel: overview, tickets with filters, tree, knot's ready and blocked queues, one ticket in
  full, and a one-way live stream that reloads the page when the backlog changes.
- Saved projects by name in `~/.config/knotview/projects.toml`.

### Fixed

- knot's `check` answers `ok: false` alongside its issues; the panel now shows them on the
  overview instead of refusing the page.
- The wheel ships the templates and static files.
- Refusals (no project, no knot, an unknown saved name, a malformed projects file) are one line on
  stderr rather than a traceback.
