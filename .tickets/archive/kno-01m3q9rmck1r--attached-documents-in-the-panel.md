---
id: kno-01m3q9rmck1r
title: Attached documents in the panel
status: closed
type: epic
priority: 2
mode: afk
created: '2026-09-29T19:20:17.042420Z'
updated: '2026-09-30T00:39:26.834747Z'
closed: '2026-09-30T00:39:26.834747Z'
assignee: ''
---

## Description

knot 0.15 lets a ticket carry documents: whole markdown files such as a spec, a plan or a transcript, each with a title and a type, stored under the tickets directory in a folder per ticket. knotview shows none of it yet. This epic surfaces documents everywhere the panel shows tickets, and adds a page to read one.

The agreed design is the mockup at https://claude.ai/artifact/45uvLj8TfGTetvbob2nzEN.

## Design

How knot stores and reports documents, measured against knot 0.15.0:

- A document lives at `<docs-dir>/<ticket-id>/<doc-id>--<slug>.md`, by default under `.tickets/docs`. Its frontmatter holds id, ticket, title, type, created and updated. The body is plain markdown.
- A document id is the owner's id plus a suffix, such as `kno-01m2kcsspxtb-d6xtb`.
- Documents never move when a ticket closes. Adding or replacing one does not change the ticket's file or its `updated` time.
- `show --json` carries `documents` (id, title, type, never the body). `list`, `ready`, `blocked` and `closed` rows carry `doc_types` only when the ticket owns some. `info` carries `doc_types`, `default_doc_type`, `required_docs`, `docs_path` and `doc_count`.
- `document list <ticket> --json` adds created and updated. `document show <id> --json` is the only read that returns a body. Both accept the `--` marker knotview uses.
- `:required-docs` in `.knot.edn` names document types a ticket must own before it may enter a status. knot refuses the move with `missing_required_docs`.

The panel stays read-only: it gains two reads, `document list` and `document show`, and no writes.

## Notes

**2026-09-30T00:39:26.123782Z**

All seven stories are closed, and so is the hang found on the way (kno-01m3qtsj503f). The panel now shows knot 0.15's attached documents:
- in every ticket list, with a multi-select filter;
- on the overview, the tree and the footer;
- on the ticket page, with missing required documents among what blocks a ticket;
- on a page of their own;
- in live reload and on the integrity card.

Each story's brainstorm, spec and plan are attached to it as knot documents.

Follow-ups filed: kno-01m3qdwrjdbx, kno-01m3qneqctfh, kno-01m3qr3peyx7, kno-01m3qtd4ax4g.
