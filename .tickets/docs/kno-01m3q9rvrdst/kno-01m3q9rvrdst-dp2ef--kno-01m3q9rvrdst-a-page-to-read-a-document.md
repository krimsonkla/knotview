---
id: kno-01m3q9rvrdst-dp2ef
ticket: kno-01m3q9rvrdst
title: A page to read a document brainstorm
type: other
created: '2026-09-30T00:08:59.406847Z'
updated: '2026-09-30T00:09:28.322771Z'
---

# kno-01m3q9rvrdst — A page to read a document brainstorm

Story: kno-01m3q9rvrdst, "A page to read a document", story 6 of epic kno-01m3q9rmck1r. Date:
2026-09-29. Mode: teams-equivalent, quality-engineer challenger, two rounds.

## Problem

knot 0.15 attaches documents to tickets, and the panel has no way to read one.

## Prior art

`Backlog.document(id)` runs `knot document show`: the one read that returns a body, raising
`MissingDocument` on `doc_not_found`, already a 404. `Backlog.documents(ticket)` runs
`document list` with times and no bodies. The ticket page reads its parent and dependencies with
extra reads and catches a missing parent locally. `prose.rendered` is CommonMark with raw HTML off
and headings demoted two levels. Every route is a GET in the `ROUTES` table.

## Approach

- **`/document/{identifier}`** reads the document, then the owning ticket's documents for the tabs
  and the ticket for the breadcrumb's title. The two owner-side reads are caught locally for
  `MissingTicket`: an orphan document, which knot still shows and `check` reports, renders with
  the bare ticket id and itself alone rather than a 404 about the ticket.
- **The resolved id decides everything current.** knot resolves a prefix id to a document; the
  current tab, the menu's entry and the position compare against the id knot answered with.
- **The body** renders through a `prose` variant that demotes headings one level (the page's title
  is the h1) and, in the same traversal, sets `doc-`-prefixed, deduplicated ids with markdown-it's
  own attribute setter and collects the outline from the inline text: the top two levels. An empty
  body says the document is empty.
- **Tabs** in type-then-title order on one line, scrolling with a faded edge; the current one
  marked `aria-current="page"`. An "all" disclosure lists every document grouped by type with its
  date, and the header shows "n of m". Both appear whenever the ticket has two or more documents;
  with one, there are no tabs. A small static script scrolls the current tab into view; nothing
  depends on it.
- **A side panel** with the ticket, type, created and updated, and the outline.

## What the challenger changed

- An owner-side refusal would reach the global `MissingTicket` handler and 404 a readable
  document; knot really does show an orphan, so it is caught and tested.
- A prefix id would mark no tab current; compare against the resolved id.
- Heading ids carry document text into the one output marked safe; set them through the
  renderer's attributes, prefix them, and test an injected heading.
- The "all" menu on overflow only needs script and cannot be asserted; show it whenever there are
  tabs.
- Outline text from the inline text, not the markdown source; outline and ids from one pass.
- An empty body is stated, not a blank article.
