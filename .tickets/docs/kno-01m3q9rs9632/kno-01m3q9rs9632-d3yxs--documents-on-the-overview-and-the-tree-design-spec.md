---
id: kno-01m3q9rs9632-d3yxs
ticket: kno-01m3q9rs9632
title: Documents on the overview and the tree design spec
type: spec
created: '2026-09-30T00:08:58.872014Z'
updated: '2026-09-30T00:09:27.324744Z'
---

# Documents on the overview and the tree Design Spec

**Story:** Documents on the overview and the tree (kno-01m3q9rs9632)
**Tier:** Feature — one overview card, the tree's rows, the footer, and one selection fix
**Brainstorm:** `docs/ai-assistant-ideation/kno-01m3q9rs9632-overview-tree-documents-brainstorm.md`

## Changes since last cycle

- The card's link is built from a copy of the selection holding only that type, through a
  `Selection` method; `query_string` itself is unchanged, since its single-valued keyword changes
  were never shaped for a repeated value.
- The footer always shows the document count, as it shows its neighbours.
- Owned types are read once per ticket when counting.

## Problem

The overview and the tree say nothing about documents, and the footer leaves them out.

## Goal

The overview counts tickets by the document types they own, the tree's rows show owned and missing
types as the lists do, and the footer counts the project's documents.

## Scope

**In scope:** the "by document" card; the tree's node and leaf tags and its tables' dashes; the
footer count; a `Selection` link to exactly one document type.
**Out of scope:** the ticket page's documents card and `#documents` anchor (story 5); the document
page (story 6).
**Non-goals:** counting documents per type; a card for tickets waiting on documents; rows for
undeclared types.

## Requirements

| ID | Priority | Requirement |
|----|----------|-------------|
| R1 | MUST | The overview shows a "by document" card with one row per declared document type, counting the tag-narrowed live tickets owning it, each linking to the tickets list filtered to exactly that type. |
| R2 | MUST | The card shows only when at least one row counts above zero, and says it counts tickets. |
| R3 | MUST | The card's link to a type carries exactly that one `doc` and no `nodocs`, whatever types the selection held, and keeps every other filter. |
| R4 | MUST | Every tree row (node and leaf) shows the ticket's owned types as tags linking to `/ticket/<id>#documents`, and for a live ticket each missing required type once as a dashed tag titled with the status it gates. |
| R5 | MUST | The tree's stray and orphan tables show dashed missing types, as its rows do. This supersedes story 3's AC-2 for the tree. |
| R6 | MUST | The footer adds "N documents" from the project's document count, zero included, as it shows the live and archived counts. |
| R7 | MUST | The table's rendered tags are unchanged by sharing their drawing with the tree. |

## Design

**Approach:** `Overview` gains `by_document`, one `Tally` per declared type over the narrowed live
tickets, each ticket's owned types read once through `Project.types_of`. The tag drawing moves from
`_ticket_table.html` into a macro both the table and the tree call. The tree page sets
`show_missing`. `layout.html`'s footer reads `project.doc_count`.

**Interfaces and contracts:** a new `Selection` method gives the query string for this selection
with its types replaced by one type and `nodocs` cleared, built from a copy of the selection the
way the chips' removal links are. `query_string(doc=...)` is not used: it appends to the selection's
own types. The macro takes the ticket, the project and whether to draw missing types as parameters,
since an imported macro does not see the importing template's context. The macro takes the ticket, the project and whether to draw missing types.

**Prior art to mirror:** the "by type" card in `overview.html` and its `Tally` rows; the docs cell
in `_ticket_table.html`.

**Key decisions:** tickets per type, since knot gives no per-type document count and one process per
ticket would run on every overview render; visibility from the rows, so tag narrowing cannot draw
an all-zero card; every gating status, since knot's statuses are a vocabulary with no "next"; the
footer's count is project-wide, including closed tickets' documents, like "archived" beside it.

## Acceptance Criteria

### Story 1: When I open the overview, I want to see which document types the work owns.

**AC-1** — Given live tickets owning spec (two) and plan (one), when the overview renders, then the
"by document" card shows spec 2, plan 1 and other 0, each linking to `/tickets?doc=<type>`.
**AC-2** — Given a chosen tag whose tickets own no documents, when the overview renders, then no
"by document" card appears.
**AC-3** — Given a selection holding `doc=plan` and `nodocs`, when the spec row's link is built,
then it carries `doc=spec`, not `doc=plan`, and no `nodocs`.
**AC-4** — Given a project whose document count is 3, when any page renders, then the footer reads
"3 documents"; given a count of 0, it reads "0 documents".

### Story 2: When I read the tree, I want to see each ticket's documents and what it lacks.

**AC-5** — Given a node owning spec and plan, when the tree renders, then its row shows spec then
plan linking to `/ticket/<id>#documents`.
**AC-6** — Given a live leaf lacking a type required for in_progress, when the tree renders, then
its row shows that type dashed, titled "needed to enter in_progress"; given a closed ticket, none.
**AC-7** — Given an orphan lacking a required type, when the tree renders, then its table row shows
the dashed tag.

### Traceability
| Story AC | Spec ACs | Notes |
|----------|----------|-------|
| A documents card counting by type, with links, only when documents exist | AC-1, AC-2, AC-3 | counts tickets per type, not documents; the mockup's document counts are not delivered as drawn |
| Tree rows show owned types, and a dashed tag for a lacking required type | AC-5, AC-6, AC-7 | every gating status, not a "next" one |
| The footer shows the document count | AC-4 | project-wide |
| Tag narrowing applies to the card | AC-2 | |

## Boundaries
- ✅ Always: read owned and missing types only through `Project`; build links only through
  `query_string`; run story 3's tests first after moving the tag drawing.
- 🚫 Never: one knot process per ticket to count documents.

## Testing Strategy
AC-1, AC-2, AC-4 to AC-7 are rendered-page tests over a declared backlog; AC-3 is a unit test of
`Selection`; R7 is held by story 3's render tests passing unchanged.

---
After implementing, compare results against each acceptance criterion above
and list any unmet requirements.
