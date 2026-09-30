---
id: kno-01m3q9rr1aer-dnzyj
ticket: kno-01m3q9rr1aer
title: Documents in the lists design spec
type: spec
created: '2026-09-30T00:08:58.460405Z'
updated: '2026-09-30T00:09:26.586588Z'
---

# Documents in the lists Design Spec

**Story:** Documents in every ticket list, with a multi-select filter (kno-01m3q9rr1aer)
**Tier:** Feature — one shared template, the filter value and the tickets page
**Brainstorm:** `docs/ai-assistant-ideation/kno-01m3q9rr1aer-list-documents-brainstorm.md`

## Changes since last cycle

- Chips: each applied filter carries the query that drops only it, so removing one type keeps the
  others; the old remover blanked a whole parameter.
- Dashed missing types show on the tickets page and both queues, where a reader picks work; not on
  overview cards or the tree's lists.
- Selection is read from the multi-valued query, not a dict that keeps one value per name.
- The table's flag defaults to off inside the partial, since most including pages pass only
  tickets.
- Encoding is tested on an existing filter (a tag) as well as a document type.

## Problem

No ticket table shows documents, and the tickets page cannot filter by them.

## Goal

Every ticket table shows the document types each ticket owns, and the tickets page filters by
owned types, by owning none, and by lacking a required type.

## Scope

**In scope:** the docs column in the shared table; missing types on the tickets page and queues; the filter,
its chips and its URL; percent-encoding links.
**Out of scope:** the overview card and tree (story 4); the ticket page's documents card and its
`#documents` anchor (story 5).
**Non-goals:** linking a tag to one document.

## Requirements

| ID | Priority | Requirement |
|----|----------|-------------|
| R1 | MUST | Every table that includes the shared ticket table shows a docs column after the title: each owned type as a tag, in declared order, linking to `/ticket/<id>#documents`. |
| R2 | MUST | On the tickets page and both queues, a live ticket's required-but-missing types show as dashed tags titled with the status they gate; other pages including the table show none. |
| R3 | MUST | The column hides when no row shows a tag and no documents filter is applied. |
| R4 | MUST | Repeated `doc` values select types; undeclared ones are dropped; a ticket matches when it owns every selected type. |
| R5 | MUST | `nodocs=1` keeps tickets owning no type, and clears any selected types. |
| R6 | MUST | `lacking=1` keeps live tickets with at least one missing required type. |
| R7 | MUST | Each selected type and each of the two options is its own chip, carrying the query that removes only itself. |
| R8 | MUST | Every link built from the selection percent-encodes its values and repeats `doc` per type. |
| R9 | MUST | The filter is checkboxes inside a disclosure, and works without script. |

## Design

**Approach:** `Selection` gains the three document fields and reads the query's repeated values;
matching takes the project; the shared table takes a flag for missing types; the tickets page sets
it. Owned and missing types come only from `Project.types_of` and `Project.missing_documents`.

**Interfaces and contracts:** `Selection.asked` takes the query's single values and, separately, the
repeated `doc` values; `Selection.matches` takes the project; a new `chips()` yields each applied
filter with its label, value and the query that drops only it; `without(label)` resolves through
it. The table's `show_missing` flag defaults to off in the partial; the column's visibility is
computed over the rows through the `Project` helpers.

**Prior art to mirror:** the assignee column's hide rule in `_ticket_table.html`; the chip loop in
`tickets.html`; `_known` in `selection.py` for dropping undeclared values.

**Key decisions:** separate parameters for the two options (a project may declare a type named
`none`); missing types only on the tickets page and the queues, where a reader picks work, and
only for live tickets (on overview cards and the tree's lists they would flood the page with gates
that mean nothing there); links to the documents card, not to a
document (rows carry type names only).

## Acceptance Criteria

### Story 1: When I scan any ticket list, I want to see which documents each ticket owns.

**AC-1** — Given a list with a ticket owning a plan and a spec, when the page renders, then its row shows spec then plan as tags linking to `/ticket/<id>#documents`.
**AC-2** — Given an overview card or the tree's lists, when they render, then no dashed tag appears; given the ready queue with a lacking ticket, a dashed tag does.
**AC-3** — Given no row owning or lacking a type and no documents filter, when the page renders, then the column is absent; given the same rows with `nodocs=1`, it is present.

### Story 2: When I look for tickets by their documents, I want to tick what I need.

**AC-4** — Given `doc=spec&doc=plan`, when the tickets page renders, then only tickets owning both appear.
**AC-5** — Given `doc=memo` in a project not declaring memo, when the page renders, then the filter is ignored.
**AC-6** — Given `nodocs=1&doc=spec`, when the page renders, then only tickets owning nothing appear and no "has spec" chip shows.
**AC-7** — Given `lacking=1` in a project requiring documents, when the page renders, then only live tickets missing a required type appear, each with dashed tags.
**AC-8** — Given two type chips, when "has spec" is removed, then the link keeps `doc=plan`; removing that leaves no `doc`.
**AC-9** — Given a tag, and a document type, each containing a space and `&`, when a link is built, then it is percent-encoded and reads back to the same value.

### Traceability
| Story AC | Spec ACs | Notes |
|----------|----------|-------|
| Every ticket table shows a docs column with one tag per owned type, linking to the document | AC-1, AC-2 | links to the ticket's documents, per the amended design |
| The column hides when no row owns a document | AC-3 | mirrors the assignee rule, filter included |
| The documents filter accepts several types and keeps tickets owning all of them | AC-4, AC-5 | |
| "none attached" and "missing a required type" filter as described, and "none attached" clears ticked types | AC-6, AC-7 | missing counts for live tickets only |
| Each ticked value is a removable chip, and the filtered view round-trips through its URL | AC-8, AC-9 | |

## Boundaries
- ✅ Always: read owned and missing types only through `Project`; build links only through `query_string`.
- 🚫 Never: read `doc_types` or `documents` in a template.

## Testing Strategy
All ACs are rendered-page tests through the TestClient over a declared backlog, plus unit tests of `Selection`.

---
After implementing, compare results against each acceptance criterion above
and list any unmet requirements.
