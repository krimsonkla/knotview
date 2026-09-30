---
id: kno-01m3q9rtgqa9-d08t5
ticket: kno-01m3q9rtgqa9
title: Documents on the ticket page design spec
type: spec
created: '2026-09-30T00:08:59.272613Z'
updated: '2026-09-30T00:09:28.078517Z'
---

# Documents on the ticket page Design Spec

**Story:** Documents on the ticket page (kno-01m3q9rtgqa9)
**Tier:** Feature — one page gains a card, a chip and rows in an existing card
**Brainstorm:** `docs/ai-assistant-ideation/kno-01m3q9rtgqa9-ticket-documents-brainstorm.md`

## Changes since last cycle

- Missing-type rows enter the graph cards' loop as a third element, not a separate block and not
  added to the blockers; the helper is `missing_by_type`, replacing the lists' dedupe accumulator.
- The fallback's wider catch is stated and tested with a refusal that is not a missing ticket.
- The card's number carries a title saying it counts blocking tickets and missing documents.

## Problem

A ticket's page does not show its documents, nor that a required document is missing.

## Goal

A reader opening a ticket sees its documents first and sees a missing required document where they
look for what blocks the ticket.

## Scope

**In scope:** the documents card, the header chip, missing-type rows in "blocked by", and the extra
read with its fallback.
**Out of scope:** changing the lists' blocked-by column; the document page (story 6). The lists'
dashed-tag title widens to name every status, through the shared helper.
**Non-goals:** a banner, a command hint, or adding documents.

## Requirements

| ID | Priority | Requirement |
|----|----------|-------------|
| R1 | MUST | A card with `id="documents"` sits after the header and above acceptance, one row per document: type tag, title linking to `/document/<id>`, id, and "updated <stamp>" when knot states it. |
| R2 | MUST | Rows come from knot's document list in the project's declared type order, then title; when that read is refused, from the documents `show` stated, without times, and the page still renders. |
| R3 | MUST | For a live ticket, each required type it lacks is one row in "blocked by": a dashed type tag, "no <type> attached", and a muted "needed to enter" naming every status that needs it. Closed tickets have none. |
| R4 | MUST | "Blocked by" shows when there are blockers or missing types, and its number counts all its rows. The word "missing" is used only for a blocker id that names no ticket. |
| R5 | MUST | The header carries "N documents" linking to `#documents` when the ticket owns some. |
| R6 | MUST | A ticket with no documents shows no card and no chip; one with no missing types adds no rows. |

## Design

**Approach:** `Pages.ticket` also reads the ticket's documents, catching a refusal and falling back
to the documents `show` stated; both are ordered by `Project.ordered`. A new `Project.missing_by_type(ticket)`
groups `missing_documents` by type, in declared type order, each with every status that needs it.
The ticket page draws its rows from it, and the lists' dashed tags take their title from it too, so
both name the same statuses.

**Interfaces and contracts:** the card's number is the count of its rows; it has always counted
closed and unknown blockers, unlike the lists' column, which counts open ones. The `#documents`
anchor cannot dangle: the only links to it are owned-type tags, drawn exactly when the card is.

The graph cards' loop gains a third element per card, the missing-type rows, empty for
"blocking", "children" and "linked"; "blocked by" carries the ticket's missing types there. Nothing
branches on a card's label and nothing is added to the ticket's blockers. A card shows when it has
references or extra rows, and its number counts both, with a title saying so. The declared test
backlog gains a switch that makes its document list refuse for a ticket that exists, which AC-2
needs, with a code other than a missing ticket, since the fallback catches every refusal of that
read (wider than `_parent_of`, which catches a missing ticket only: `show` has already succeeded,
so the only refusal left to catch is one about the documents themselves).

**Prior art to mirror:** `_parent_of` for the degradable read; `_ticket_table.html`'s dashed tags
and "needed to enter" wording; the graph cards in `ticket.html`.

## Acceptance Criteria

### Story 1: When I open a ticket, I want its documents first.

**AC-1** — Given a ticket owning a plan and a spec, when its page renders, then a card with
`id="documents"` above acceptance lists spec then plan, each with its type, a link to
`/document/<id>`, its id and "updated" with its time; the header reads "2 documents" linking to
`#documents`.
**AC-2** — Given knot refusing the document list, when the page renders, then it answers 200 with
the rows from `show` and no times.
**AC-3** — Given a ticket owning no documents, when its page renders, then there is no card and no
chip.

### Story 2: When a ticket cannot move for a missing document, I want to see it with its blockers.

**AC-4** — Given a live ticket lacking spec and plan, required to enter in_progress, when its page
renders, then "blocked by" holds two rows with dashed tags, "no spec attached" and "needed to enter
in_progress", and its number includes them.
**AC-5** — Given a type required by two statuses, when the page renders, then it is one row naming
both.
**AC-6** — Given a closed ticket lacking a required type, when its page renders, then "blocked by"
has no document row.
**AC-7** — Given a ticket with no blockers and no missing types, when its page renders, then there
is no "blocked by" card; a document row never says "missing".

### Traceability
| Story AC | Spec ACs | Notes |
|----------|----------|-------|
| The documents card lists every document with type, title, id and last change, above acceptance | AC-1, AC-2 | |
| Rows order by the project's type order, then title | AC-1 | |
| A missing required type appears as a quiet row in blocked by and counts toward its number | AC-4, AC-5, AC-6 | live tickets only; every gating status |
| A ticket with no documents and no missing types shows neither | AC-3, AC-7 | |

## Boundaries
- ✅ Always: owned and missing types only through `Project`; the missing-type look from story 3.
- 🚫 Never: a banner or a command hint; let the document read fail the page.

## Testing Strategy
Every AC is a rendered-page test over a declared backlog; AC-2 uses a backlog whose document list
refuses.

---
After implementing, compare results against each acceptance criterion above
and list any unmet requirements.
