---
id: kno-01m3w61pvk11-dh5p0
ticket: kno-01m3w61pvk11
title: Epic children design spec
type: spec
created: '2026-10-01T17:01:31.979961Z'
updated: '2026-10-01T17:01:31.979961Z'
---

# Epic children design spec

**Story:** On a ticket page, exclude closed children and order children by status (kno-01m3w61pvk11)
**Tier:** Feature — one page's two cards and one URL parameter

## Requirements

| ID | Priority | Requirement |
|----|----------|-------------|
| R1 | MUST | The children card and the siblings card list tickets in the project's declared status order; undeclared statuses after the declared ones; missing references last; knot's order within each. |
| R2 | MUST | `?children=live` hides children in a terminal status; any other value, or none, shows all. |
| R3 | MUST | Shown: the heading reads "children N" with a link "hide closed (C)" when C closed children exist. Hidden: "children S of N" with a link "show closed". The card stays whenever it has rows or hid any. |
| R4 | MUST | Each card's count is counted from the rows it draws, computed in the page, not the template. |
| R5 | MUST | No link on the page carries `children=` except the toggle. |
| R6 | MUST | Blocked by, blocking and linked keep knot's order. |

## Acceptance Criteria

**AC-1** — Given children closed, open and in_progress in that order, when the page renders, then they list open, in_progress, closed.
**AC-2** — Given an epic with 3 live and 4 closed children, when `?children=live` is asked, then the card lists the 3 and reads "children 3 of 7" with "show closed" linking to the page without the parameter.
**AC-3** — Given the same epic without the parameter, when the page renders, then it reads "children 7" with "hide closed (4)" linking to `?children=live`.
**AC-4** — Given an epic whose children are all closed, when `?children=live` is asked, then the card stays and reads "children 0 of 7".
**AC-5** — Given `?children=bogus`, when the page renders, then every child shows.
**AC-6** — Given the page, when it renders, then no href other than the toggle holds `children=`.
**AC-7** — Given a missing child reference and one with an undeclared status, when the page renders, then the undeclared one sorts after the declared statuses and the missing one last.
**AC-8** — Given a parent whose children have mixed statuses, when a child's page renders, then the siblings card lists them in status order and counts the rows it draws.
**AC-9** — Given the epic, when its toggle is followed from shown to hidden and back, then the heading reads "children 7", then "children 3 of 7", then "children 7" again.
**AC-10** — Given an epic with no closed children, when its page renders, then there is no toggle.

## Design note

R1, R3 and R4 take the children card out of the shared loop's single shape: the four graph cards are drawn by one macro, which the children card calls with its own count, toggle and keep-when-hidden flag, rather than a fifth tuple position or a branch on the card's label. The tree's children are not reordered here; that is filed as its own ticket.
