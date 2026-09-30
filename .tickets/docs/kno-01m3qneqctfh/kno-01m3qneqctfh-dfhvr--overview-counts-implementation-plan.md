---
id: kno-01m3qneqctfh-dfhvr
ticket: kno-01m3qneqctfh
title: Overview counts implementation plan
type: plan
created: '2026-09-30T04:04:23.719747Z'
updated: '2026-09-30T04:04:23.719747Z'
---

# Overview counts implementation plan

**Spec:** `kno-01m3qneqctfh-overview-counts-spec.md`. **Test route:** strict.

## Task 1: Tests
- [ ] AC-1 and AC-4 in tests/panel/test_overview.py: render with the filter set and without; the
  bodies match apart from nothing, and no href holds `closed=`, `type=bug`, `doc=spec`,
  `assignee=someone`, `q=` or `lacking=`, except the terminal rows' own `closed=1`.
- [ ] AC-2, parametrized over card and row, including the queues card: in a new file,
  tests/panel/test_overview_links.py, a backlog built there (not by editing the shared
  DeclaredBacklog) holding a live chore, a closed chore, a ticket owning an `other` document and
  an unassigned one. Parse each tally's count and href, GET the href with the same client, and
  count the ticket rows the page lists.
- [ ] AC-3: the exact query of one row per card.

## Task 2: The fix
- [ ] `Pages.overview` passes `selection=Selection()`; its docstring states the rule.
- [ ] overview.html: a comment on the terminal rows building their own `closed=1`.
- [ ] README: check the overview row for the carried-selection claim.

## Task 3: Gate
- [ ] pytest, ruff, black, pylint, prek; /code-review high until approved.
