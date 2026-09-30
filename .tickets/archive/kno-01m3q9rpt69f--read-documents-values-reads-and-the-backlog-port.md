---
id: kno-01m3q9rpt69f
title: 'Read documents: values, reads and the backlog port'
status: closed
type: task
priority: 2
mode: afk
created: '2026-09-29T19:20:19.526573Z'
updated: '2026-09-29T22:04:24.967669Z'
closed: '2026-09-29T21:32:18.601047Z'
assignee: Jason Risch
parent: kno-01m3q9rmck1r
acceptance:
- title: Document metadata from show, the listings and info reaches the value types
  done: true
- title: document list and document show are in READS and parsed into Document values
  done: true
- title: An unknown document id raises MissingDocument
  done: true
- title: The missing-required-types helper is tested for a project with and without :required-docs
  done: true
- title: The fidelity test checks the new envelopes against real knot 0.15.0
  done: true
deps:
- kno-01m3q9rnkpy7
---

## Description

knotview's reading layer knows nothing of documents. Teach it to read them, so every page after this story can show them without touching knot directly.

## Design

- A `Document` value (id, ticket, title, type, created, updated, and body when read singly), and a `document_from` reader in `knot_envelope`.
- `Ticket` gains `documents` from `show` and `doc_types` from listing rows; absent means none.
- `Project` gains `doc_types`, `default_doc_type`, `required_docs` (status to types) and `doc_count` from `info`.
- `READS` gains `document list` and `document show`; the test that `READS` holds no write verb still holds.
- `Backlog` gains `documents(ticket)` and `document(id)`. An unknown document id raises a new `MissingDocument`, served as a 404 like `MissingTicket`. `DeclaredBacklog` gains the same, so pages are tested without a process.
- A helper answers "which required types does this ticket lack for its next status", used by the ticket page and the tree.

## Notes

**2026-09-29T20:45:51.465847Z**

Starting work on this task.

**2026-09-29T21:31:58.537603Z**

Implementation artifacts attached
branch: jr/kno-01m3q9rmck1r-attached-documents commit: e9ee21d7cf7d13b549ff98ee64eb11752ac37614
- Brainstorm: docs/ai-assistant-ideation/kno-01m3q9rpt69f-reading-documents-brainstorm.md @ e9ee21d7cf7d13b549ff98ee64eb11752ac37614
- Spec: docs/ai-assistant-ideation/kno-01m3q9rpt69f-reading-documents-spec.md @ e9ee21d7cf7d13b549ff98ee64eb11752ac37614
- Plan: docs/ai-assistant-ideation/kno-01m3q9rpt69f-reading-documents-plan.md @ e9ee21d7cf7d13b549ff98ee64eb11752ac37614

**2026-09-29T21:32:15.779512Z**

Task completed: the reading layer knows documents. A Document value holds id, owner, title and type, plus created, updated and body as None when knot did not state them (the command does not report them, or knot answered null) and as empty text only when stated empty. Tickets carry documents from show and doc_types from listing rows. Project carries doc_types, required_docs (declared statuses first) and doc_count, and four helpers pages use instead of the raw fields: ordered (declared type order, then title ignoring case, undeclared types last), ordered_types, types_of (skipping an untyped document) and missing_documents (every status whose requirement a ticket does not meet, its own included). knot itself gives documents in id order from show and types alphabetically from listings, so the panel imposes its own order. The two new reads, document list and document show, map knot's not_found to MissingTicket and doc_not_found to a new MissingDocument, served as its own 404; knot's three document writes joined the read-only guard's list. The probe now requires a spec and a plan for in_progress, recorded through info. The fidelity test runs both reads against knot 0.15.0, including a prefix id resolving to the whole id. 267 tests at 100 percent. default_doc_type was left out: only document creation reads it. Story 3's design was amended: its type tags link to the ticket's documents card, since listing rows carry type names, never document ids.

**2026-09-29T21:32:17.160588Z**

Acceptance criteria ticked as verified: Document metadata from show, the listings and info reaches the value types, document list and document show are in READS and parsed into Document values, An unknown document id raises MissingDocument, The missing-required-types helper is tested for a project with and without :required-docs, The fidelity test checks the new envelopes against real knot 0.15.0

**2026-09-29T22:04:06.493075Z**

Implementation artifacts attached
branch: jr/kno-01m3q9rmck1r-attached-documents commit: 1b97d98be6444c7fee52dd552615beda9e028052
- Brainstorm: docs/ai-assistant-ideation/kno-01m3q9rpt69f-reading-documents-brainstorm.md @ 1b97d98be6444c7fee52dd552615beda9e028052
- Spec: docs/ai-assistant-ideation/kno-01m3q9rpt69f-reading-documents-spec.md @ 1b97d98be6444c7fee52dd552615beda9e028052
- Plan: docs/ai-assistant-ideation/kno-01m3q9rpt69f-reading-documents-plan.md @ 1b97d98be6444c7fee52dd552615beda9e028052

**2026-09-29T22:04:24.967669Z**

The earlier artifacts note pinned e9ee21d, a commit from before the docs were committed; the latest artifacts note pins them at a commit that holds them.
