---
id: kno-01m3q9rs9632-dcvzy
ticket: kno-01m3q9rs9632
title: Documents on the overview and the tree brainstorm
type: other
created: '2026-09-30T00:08:58.595023Z'
updated: '2026-09-30T00:09:26.824388Z'
---

# kno-01m3q9rs9632 — Documents on the overview and the tree brainstorm

Story: kno-01m3q9rs9632, "Documents on the overview and the tree", story 4 of epic
kno-01m3q9rmck1r. Date: 2026-09-29. Mode: teams-equivalent, quality-engineer challenger, two
rounds.

## Problem

The overview and the tree say nothing about documents, and the footer's counts leave them out.

## Prior art

`Overview.over` in `overview.py` builds one `Tally` per declared value over the snapshot's live
tickets, zeros kept, and the overview page narrows those tickets by the tag cookie before
counting. Each "by" card counts tickets. Story 3 draws owned and dashed missing types in
`_ticket_table.html`, dashes only where a page sets `show_missing`. `knot info` gives `doc_count`
for the whole project; listing rows give type names only, with no per-type document counts.

## Approach

- **A "by document" card** beside the other "by" cards: one row per declared document type,
  counting the tag-narrowed live tickets that own it, each linking to `/tickets?doc=<type>`. A
  muted line says it counts tickets, and that a ticket may own several documents. It shows when
  any row is above zero, so the rows and the rule come from the same narrowed set.
- **`query_string(doc=X)` replaces** the selection's types with exactly X and clears `nodocs`,
  rather than appending, so a link that changes the type goes to the list its count describes.
- **The tree's rows** show the same tags as the table, through one macro shared by both: owned
  types linking to `/ticket/<id>#documents` and, for live tickets, dashed missing types from every
  status that gates them. The tree page sets `show_missing`, so its stray and orphan tables agree
  with its rows. This supersedes story 3's AC-2 for the tree.
- **The footer** adds "N documents" from `doc_count` when it is above zero: project-wide,
  including closed tickets' documents, like "archived" beside it.

## What the challenger changed

- Counting documents per type needs a process per ticket on the most-rendered page; tickets per
  type it is, named as such. The mockup's document counts are not delivered as drawn.
- The card's visibility read `doc_count`, which is not narrowed; a narrowed tag would draw all
  zeros. Visibility now comes from the rows.
- `query_string(doc=...)` appended to the selection's types, so a row could link to a narrower
  list than it counted. Fixed at the source.
- "Documents" on the card and on the footer meant two things; the card is "by document" and says
  it counts tickets.
- "Next status" is undefined for a status vocabulary; every gating status, as the lists show.
- An undeclared type gets no row: `Selection` would drop it from the link, and knot's `check`
  already reports it in the integrity card.
