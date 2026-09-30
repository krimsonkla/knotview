---
id: kno-01m3q9rtgqa9-ddxxv
ticket: kno-01m3q9rtgqa9
title: Documents on the ticket page brainstorm
type: other
created: '2026-09-30T00:08:59.000966Z'
updated: '2026-09-30T00:09:27.578363Z'
---

# kno-01m3q9rtgqa9 — Documents on the ticket page brainstorm

Story: kno-01m3q9rtgqa9, "Documents on the ticket page", story 5 and the last of epic
kno-01m3q9rmck1r. Date: 2026-09-29. Mode: teams-equivalent, quality-engineer challenger, two
rounds.

## Problem

The ticket page does not show a ticket's documents, and does not say when a required document is
missing, which is often why a ticket cannot move.

## Prior art

`Pages.ticket` reads `show` (documents with id, title and type), the parent and the dependency
tree. `document list` adds times. `Project.ordered` and `Project.missing_documents` from story 2;
the dashed type tag and "needed to enter" wording from story 3. The graph section draws "blocked
by", "blocking", "children" and "linked" cards, each counting its rows.

## Approach

- **A documents card** with `id="documents"` after the header, above acceptance: type tag, title
  linking to `/document/<id>`, id, and "updated <stamp>" when knot states it. Rows from
  `document list` in declared type order then title. When that read is refused, the rows come
  from `show`'s documents without times rather than the page failing.
- **Missing types in "blocked by"**, for live tickets only: one row per missing type, a dashed
  type tag, "no <type> attached", and a muted "needed to enter <statuses>" naming every status that
  needs it. The card shows when there are blockers or missing types; its number counts its rows,
  as it always has (closed and unknown blockers included). The word "missing" stays with the
  unknown-id rows.
- **A header chip** "N documents" linking to `#documents`, only when the ticket owns some.
- The `#documents` anchor cannot dangle: the only links to it are owned-type tags, which exist
  exactly when the card does.

## What the challenger changed

- The new read degrades instead of adding a way for the page to fail.
- Document rows do not reuse "missing", which already means an id that names no ticket.
- The card's count is stated as rows, which it already was; the list column is unchanged.
- Every status that needs a type is named, since the card has room the column does not.
- Live tickets only, in the criteria; no "created" branch, which real knot never reaches.
