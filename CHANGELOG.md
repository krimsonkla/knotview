# Changelog

All notable changes are recorded here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

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
