---
id: kno-01m3qneqctfh-dpk5p
ticket: kno-01m3qneqctfh
title: Overview counts design spec
type: spec
created: '2026-09-30T04:04:23.564495Z'
updated: '2026-09-30T04:04:23.564495Z'
---

# Overview counts design spec

**Story:** Overview counts disagree with their links when the URL carries closed=1 (kno-01m3qneqctfh)
**Tier:** Small — one page stops reading its query string

## Requirements

| ID | Priority | Requirement |
|----|----------|-------------|
| R1 | MUST | The overview ignores its query string: every card links with only the filter its row means (one parameter; two, `status=X&closed=1`, for terminal rows). |
| R2 | MUST | Each card row's count equals the number of rows the page its link opens lists (a filtered tickets list, or a queue page for the queues card, whose links never carried a query and hold for that reason), while knot's own check is clean: a ticket in a terminal status that knot has not archived is listed under its status but not counted among the closed. |
| R3 | MUST | `Pages.overview`'s docstring no longer claims it carries a reader's selection, and states the count-equals-list rule and its clean-check assumption. |

The embedded tables then behave on the overview as on the tree: the assignee column's rule, the
docs column's rule and the sort headers read an empty selection.

## Acceptance Criteria

**AC-1** — Given `/?closed=1&type=bug&doc=spec&assignee=someone&q=z&lacking=1`, when the overview
renders, then no card link's query holds any parameter but its own row's (the complement, so every
filter the selection knows is covered, not only these six).
**AC-2** — Given each card row (by type, status, terminal status, priority, queues, document),
when its link is followed, then the page lists exactly as many tickets as the row counts.
**AC-3** — Given the overview, when it renders, then each card link's query is exactly its row's
own filter.
**AC-4** — Given a filter in the overview's URL, when the page renders, then it answers 200 with the
same page as without it.
