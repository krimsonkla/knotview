---
id: kno-01m3q9rr1aer-dsxra
ticket: kno-01m3q9rr1aer
title: Documents in the lists brainstorm
type: other
created: '2026-09-30T00:08:58.182630Z'
updated: '2026-09-30T00:09:26.076844Z'
---

# kno-01m3q9rr1aer — Documents in the lists brainstorm

Story: kno-01m3q9rr1aer, "Documents in every ticket list, with a multi-select filter", story 3 of
epic kno-01m3q9rmck1r. Date: 2026-09-29. Mode: teams-equivalent, quality-engineer challenger, two
rounds.

## Problem

Every ticket table is blind to documents, and a reader cannot ask for the tickets that own a spec,
own nothing, or lack what their status requires.

## Prior art

The shared `_ticket_table.html` hides the assignee column when every row agrees and the assignee
filter is unset. `Selection` in `selection.py` carries every filter as one string field, builds
every link through `query_string`, and gives one removable chip per filter through `applied` and
`without`.

## Approach

- **A docs column** after the title: each owned type as a tag, in the project's declared order
  (`Project.types_of`), linking to `/ticket/<id>#documents`. A listing row carries type names only
  and a ticket may own several documents of one type, so a tag cannot name one document.
- **Missing types, on the tickets page only.** There, a live ticket's required-but-missing types
  show as dashed tags titled with the status they gate. Other pages include the table with the
  flag off, so a queue or an overview card does not fill with gates that mean nothing there.
- **The hide rule mirrors the assignee column's in full:** the column hides only when no row shows
  a tag and no documents filter is applied.
- **The filter** is a native disclosure of checkboxes, no script. Types travel as repeated `doc`
  values, undeclared ones dropped; "none attached" is `nodocs=1` and "missing a required type" is
  `lacking=1`. Separate parameters because knot accepts a project declaring a document type named
  `none`. Ticking several types keeps tickets owning all of them, as the tag filter does. "None
  attached" clears the ticked types.
- **Matching** gains the project: owned types from `types_of`, missing from `missing_documents`,
  which counts only for live tickets, for the same reason the dashes do.
- **Chips:** one per ticked type ("has spec"), plus the two booleans, each removing only itself.
- **Links are percent-encoded,** because this adds a third project-declared string to the URL.

## What the challenger changed

- A sentinel inside `doc` would collide with a declared type; separate parameters.
- The old `without` dropped a whole parameter, so removing one type chip would clear them all.
- Owned types alone would make the "missing" filter's rows show no reason; missing types shown.
- Half the assignee hide rule would hide the column exactly when its own filter is on.
- Showing missing types in every table would flood queues and overview cards; tickets page only.
