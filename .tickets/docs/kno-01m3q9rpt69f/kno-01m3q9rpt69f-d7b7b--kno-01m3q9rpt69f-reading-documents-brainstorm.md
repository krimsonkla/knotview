---
id: kno-01m3q9rpt69f-d7b7b
ticket: kno-01m3q9rpt69f
title: Reading documents brainstorm
type: other
created: '2026-09-30T00:08:57.771958Z'
updated: '2026-09-30T00:09:25.343448Z'
---

# kno-01m3q9rpt69f — Reading documents brainstorm

Story: kno-01m3q9rpt69f, "Read documents: values, reads and the backlog port", story 2 of epic
kno-01m3q9rmck1r. Date: 2026-09-29. Mode: teams-equivalent, quality-engineer challenger, two
rounds.

## Problem

knot 0.15 reports documents on `show`, on listing rows, in `info`, and through two document
reads, but knotview's values and reading layer ignore all of it. The later stories render
documents in lists, the overview and tree, the ticket page and a document page; they need
values to render from, never knot directly.

## Prior art

`Ticket` and `Project` are frozen, keyword-only dataclasses filled by `ticket_from` and
`project_from` in `knot_envelope.py`. `KnotCommand.ticket()` turns knot's `not_found` into
`MissingTicket`, which the app serves as a 404. The `Backlog` protocol is implemented by
`KnotCommand`, by `DeclaredBacklog` in the panel tests, and by a fake knot script that serves
recordings. This story mirrors each of those.

## What the probing found

- knot uses two orders for the same ticket: `show` and `document list` give documents in id
  order, while a listing row's `doc_types` is alphabetical. Neither is the project's declared
  `doc_types` order.
- `show` carries `documents` but no `doc_types`; listing rows carry `doc_types` but no
  `documents`.
- `knot check` does not report a ticket that already sits in a status whose required documents
  it lacks; knot enforces the rule only when a ticket moves.
- `document list` on an unknown ticket answers `not_found`; `document show` on an unknown
  document answers `doc_not_found`.

## Approach

- **One `Document` value** with id, ticket, title and type always, and created, updated and body
  as `str | None`, where None means the command that produced the value did not read it and ""
  means knot stated it empty. From `show`: ticket is the shown ticket's id, the rest None. From
  `document list`: created and updated. From `document show`: all of it. The owner is never parsed
  from the document id.
- **`Ticket`** gains `documents` (from `show`) and `doc_types` (from rows), raw as knot gives them.
- **`Project`** gains `doc_types`, `required_docs` as (status, types) pairs (declared statuses in
  declared order, then any others in `info`'s order) and `doc_count`, and four helpers, which are
  the only way pages read documents:
  - `ordered(documents)` — declared type order, then title ignoring case, unknown types last;
  - `ordered_types(types)` — the same order for bare type names;
  - `types_of(ticket)` — the types a ticket owns, from its documents when it has them and its
    `doc_types` otherwise, ordered;
  - `missing_documents(ticket)` — (status, missing types) for every status whose requirement the
    ticket does not meet, its current status included, terminal tickets included. Pages filter.
- **Reads.** `READS` gains `document list` and `document show`. `KnotCommand.documents(ticket)`
  and `document(id)`: `not_found` becomes `MissingTicket`, `doc_not_found` a new
  `MissingDocument` (also a 404), anything else stays `UnreadableBacklog`.
- **Fixtures.** The main probe's `.knot.edn` gains `:required-docs {"in_progress" ["spec"
  "plan"]}`, recorded through `info`; the in-progress child owns only a spec and the orphan owns
  nothing, so real "missing" cases exist. A project without requirements is a declared `Project`
  in the tests. Ordering is asserted only over declared values whose id, created, title and
  alphabetical orders all disagree; no test asserts knot's own order.

## Rejected

- Inheriting knot's order: knot has two, so pages fed by `show` and by rows would disagree.
- "Every status after the current one": knot's statuses are a vocabulary, not a sequence.
- `default_doc_type` on `Project`: only document creation reads it, and the panel never writes.
- A second probe for `:required-docs`: a second `info` recording to keep in step, for nothing the
  main probe cannot show.

## Consumers named

`documents(ticket)` serves story 5's documents card and story 6's "all" menu, both of which show a
document's date, which `show` does not carry. `missing_documents` serves story 5's blocked-by row,
story 4's tree tags and story 3's filter.
