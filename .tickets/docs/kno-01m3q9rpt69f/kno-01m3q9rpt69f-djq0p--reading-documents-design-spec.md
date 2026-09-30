---
id: kno-01m3q9rpt69f-djq0p
ticket: kno-01m3q9rpt69f
title: Reading documents design spec
type: spec
created: '2026-09-30T00:08:58.044782Z'
updated: '2026-09-30T00:09:25.827586Z'
---

# Reading documents Design Spec

**Story:** Read documents: values, reads and the backlog port (kno-01m3q9rpt69f)
**Tier:** Feature — new values and two reads across the values and reading layers, no pages
**Brainstorm:** `docs/ai-assistant-ideation/kno-01m3q9rpt69f-reading-documents-brainstorm.md`

## Changes since last cycle

- A document's body is kept exactly as knot states it, so an empty body stays "" and a missing
  one is None; it is not read through the helper that turns blank text into None.
- The read-only guard's list of write verbs gains `document add`, `document replace` and
  `document delete`, so the guard covers the document group.
- `Project`'s helpers take a `Ticket`, reversing the values layer's usual direction; that is now a
  stated decision.
- The reads take identifiers: `documents(ticket_id)` and `document(document_id)`.
- `MissingDocument` has its own 404 handler and its own advice.
- A listing row carries only type names, so story 3's type tags link to the ticket's documents
  card, not to a document; story 3's ticket is amended.

## Problem

knot 0.15 reports documents on `show`, on listing rows, in `info` and through two document reads,
and knotview ignores all of it. The epic's page stories need values to render from. knot also
gives documents in two different orders depending on the command, and enforces required
documents only when a ticket moves, so neither order nor the gap can be taken from knot as is.

## Goal

The reading layer exposes documents, their order, the types a ticket owns and the required types it
lacks, so every later page reads documents only through these values.
**Success signals:** every story AC below passes; the fidelity test passes against knot 0.15.0; the
suite holds 100 percent.

## Scope

**In scope:** the `Document` value; document fields on `Ticket` and `Project`; the four `Project`
helpers; the two reads on `KnotCommand` and the `Backlog` protocol; `MissingDocument` and its 404;
`DeclaredBacklog` and the fake knot; recording `:required-docs`.
**Out of scope:** any page or template (stories 3 to 6); live reload and integrity display of
documents (story 7).
**Non-goals:** writing documents; `default_doc_type`, which only creation reads.

## Requirements

| ID | Priority | Requirement |
|----|----------|-------------|
| R1 | MUST | A `Document` has id, ticket, title and type always, and created, updated and body as optional text where absent means "not read by this command" and empty means "knot stated it empty". The body is kept exactly as stated. The class docstring states the rule. |
| R2 | MUST | `Ticket` carries `documents` from `show` (each with `ticket` set to the shown ticket's id, never parsed from the document id) and `doc_types` from listing rows. |
| R3 | MUST | `Project` carries `doc_types` in declared order, `required_docs` as (status, types) pairs with declared statuses first in declared order and any others after in `info`'s order, and `doc_count`. |
| R4 | MUST | `Project.ordered(documents)` orders by declared type order, then title ignoring case, with undeclared types last; `ordered_types(types)` orders bare type names the same way. |
| R5 | MUST | `Project.types_of(ticket)` is the ordered types a ticket owns: from its documents when it has any, else from its `doc_types`. |
| R6 | MUST | `Project.missing_documents(ticket)` lists (status, missing types) for every status whose requirement the ticket does not meet, including its current status and terminal tickets, in `required_docs` order; empty when nothing is required. |
| R7 | MUST | `READS` gains `document list` and `document show`; the guard's list of write verbs gains `document add`, `document replace` and `document delete`, and the guard passes. |
| R8 | MUST | `Backlog` gains `documents(ticket_id)` (from `document list`, with created and updated) and `document(document_id)` (from `document show`, with body). |
| R9 | MUST | knot's `not_found` from either read raises `MissingTicket`; `doc_not_found` raises `MissingDocument`; any other refusal stays `UnreadableBacklog`. |
| R10 | MUST | The app answers `MissingDocument` with its own 404 handler, naming the document and advising a look at the owning ticket's documents. |
| R11 | MUST | The main probe's `.knot.edn` declares `:required-docs {"in_progress" ["spec" "plan"]}`; the recordings are re-recorded and the fidelity test passes. |
| R12 | MUST | `DeclaredBacklog` and the fake knot answer both new reads. |

## Design

**Approach:** Mirror `Ticket`/`ticket_from` and `Project`/`project_from`: a frozen, keyword-only
`Document` read by a `document_from`, with the new fields read tolerantly as today. Ordering and
the required-documents gap live on `Project`, because both depend on the project's declared
types and statuses; pages call the helpers and never read the raw fields.

**Components and responsibilities:**
- *`Document`* — one document's metadata, and its body when read singly.
- *`Ticket`* — gains the raw `documents` and `doc_types` knot states.
- *`Project`* — gains the document configuration and the four helpers.
- *`MissingDocument`* — a kind of `UnreadableBacklog`, served as a 404.
- *`KnotCommand`* — the two reads and the refusal mapping.
- *`Backlog`*, *`DeclaredBacklog`*, *the fake knot* — the same two reads.

**Interfaces and contracts:**
- `documents(ticket)` returns the ticket's documents with created and updated; a ticket owning none
  returns an empty tuple.
- `document(id)` returns one document with its body.
- Neither read orders its result; ordering is `Project.ordered`.

**Data and state:** no state; the recordings change only where `:required-docs` appears.

**Prior art to mirror:** `src/knotview/reading/knot_envelope.py` (`ticket_from`, `project_from`,
`_text`, `_words`), `src/knotview/reading/knot_command.py` (`ticket()` and its refusal mapping),
`src/knotview/values/missing_ticket.py`, and the handler registration in
`src/knotview/panel/app.py`.

**Key decisions:**
- The panel imposes its order — knot gives `show` documents by id and row types alphabetically.
- The gap covers every status including the current one — knot's statuses are a vocabulary, and
  knot never reports a ticket already sitting in a gated status without its documents.
- `types_of` is the one place owned types are read — `show` carries no `doc_types` and rows carry
  no `documents`.
- `Project`'s helpers take a `Ticket` and `Document`s, where `Ticket.open_blockers` takes bare
  statuses to keep values independent — the helpers need both the project's configuration and the
  ticket's documents, and there is no cycle, since tickets never import `Project`.

**Alternatives rejected:**
- Separate classes for partial and whole documents — one class with optional fields that say "not
  read" is enough and keeps templates simple.
- A second probe for `:required-docs` — a second `info` recording for nothing the main probe
  cannot show.

## Acceptance Criteria

### Story 1: When knot reports documents, I want them as values, so pages never read knot's shapes.

**AC-1** — show and rows
Given the recorded `show-parent` and `list`
When they are read
Then the parent's `documents` holds its two documents with `ticket` equal to the parent's id and no times or body, and each list row's `doc_types` equals the recorded list.

**AC-2** — info
Given the recorded `info`
When it is read
Then `doc_types` is spec, plan, other; `required_docs` is `(("in_progress", ("spec", "plan")),)`; and `doc_count` is 4.

**AC-3** — document list and show
Given the fake knot serving the recordings
When `documents` of the parent and `document` of its spec are read
Then the first gives two documents with created and updated and no body, and the second gives the spec with its body.

**AC-4** — refusals
Given the fake knot answering `doc_not_found`, then `not_found`, then another refusal
When `document` or `documents` is read each time
Then they raise `MissingDocument`, `MissingTicket` and `UnreadableBacklog` in turn.

**AC-5** — the 404
Given a backlog whose `document` raises `MissingDocument`
When any page asks for it
Then the app answers 404 with the ticket list offered.

### Story 2: When a page shows documents, I want one order and one answer for what is owned and missing.

**AC-6** — order
Given a declared project and documents whose id, created, title and alphabetical type orders all disagree
When they are ordered
Then they follow declared type order, then title ignoring case, with an undeclared type last.

**AC-7** — owned types
Given one ticket with documents and no `doc_types` and another with `doc_types` and no documents
When `types_of` is asked of each
Then both give their types in declared order.

**AC-8** — missing, with requirements
Given the recorded project and the in-progress child owning only a spec
When `missing_documents` is asked
Then it gives `(("in_progress", ("plan",)),)`, and the orphan, owning nothing, gives `(("in_progress", ("spec", "plan")),)`.

**AC-9** — missing, without requirements
Given a declared project with no `:required-docs`
When `missing_documents` is asked of any ticket
Then it gives an empty tuple.

**AC-10** — an undeclared status keeps its requirement
Given `info` whose `required_docs` names a status the project does not declare
When the project is read
Then that requirement follows the declared ones rather than being dropped.

### Traceability
| Story AC | Spec ACs | Requirements | Notes |
|----------|----------|--------------|-------|
| Document metadata from show, the listings and info reaches the value types | AC-1, AC-2 | R1–R3 | `default_doc_type` dropped by the brainstorm |
| document list and document show are in READS and parsed into Document values | AC-3 | R7, R8, R12 | |
| An unknown document id raises MissingDocument | AC-4, AC-5 | R9, R10 | also maps `not_found` to `MissingTicket` |
| The missing-required-types helper is tested for a project with and without :required-docs | AC-8, AC-9, AC-10 | R6 | |
| The fidelity test checks the new envelopes against real knot 0.15.0 | AC-2 | R11 | |

## Boundaries
- ✅ Always: read new fields tolerantly, as `_text` and `_words` do; re-record through the recorder.
- ⚠️ Ask first: changing an existing `Ticket` or `Project` field.
- 🚫 Never: parse a document's owner from its id; assert knot's own document order in a test.

## Testing Strategy
| AC | Level | Notes |
|----|-------|-------|
| AC-1, AC-2 | unit | over recordings |
| AC-3, AC-4 | unit | through the fake knot |
| AC-5 | integration | TestClient over a declared backlog |
| AC-6 to AC-10 | unit | over declared values |
| R11 | integration | slow fidelity test |

## Risks and Open Questions
- [Note from brainstorm] The ticket page will run two knot processes per load (`show` and
  `document list`) — affects story 5, accepted.

## Assumptions
1. Title order ignores case using Python's `casefold` — Impact: LOW
   Correct this if: a reader expects a locale-aware order.

---
After implementing, compare results against each acceptance criterion above
and list any unmet requirements.
