---
id: kno-01m3q9rvrdst-dhbbe
ticket: kno-01m3q9rvrdst
title: A page to read a document design spec
type: spec
created: '2026-09-30T00:08:59.691730Z'
updated: '2026-09-30T00:09:28.851363Z'
---

# A page to read a document Design Spec

**Story:** A page to read a document (kno-01m3q9rvrdst)
**Tier:** Feature — one new read-only page, a renderer variant, and a route
**Brainstorm:** `docs/ai-assistant-ideation/kno-01m3q9rvrdst-document-page-brainstorm.md`

## Changes since last cycle

- The test double resolves a prefix as knot does (R10), and an ambiguous prefix, which knot
  refuses with `ambiguous_doc`, is a 404 like an unknown id (R8).
- An outline entry's text is plain text with any markup dropped, autoescaped by the template; the
  body HTML stays the only value the page marks safe (R5).
- `rendered` and the new function share one token walk, so demotion is written once.
- R1 is held by a deliberate edit to both lists in `tests/panel/test_routes.py`.

## Problem

knot 0.15 attaches documents to tickets, and the panel cannot show one.

## Goal

A reader opens `/document/<id>` and reads the document in full, moves between its ticket's other
documents, and gets back to the ticket.

## Scope

**In scope:** the route and page; the renderer variant with heading ids and an outline; tabs, the
"all" menu and the position; the orphan and prefix-id cases.
**Out of scope:** the ticket page's documents card and its links here (story 5); live reload of
document changes (story 7).
**Non-goals:** editing, raw download, rendering a document's HTML.

## Requirements

| ID | Priority | Requirement |
|----|----------|-------------|
| R1 | MUST | `/document/<id>` is a GET in the route table, reading the document with knot's document read. |
| R2 | MUST | The page shows a breadcrumb to the owning ticket (its title, or its bare id when knot cannot read it), the document's title as the page's only h1, its type tag, its id and its last change. |
| R3 | MUST | The body renders through the safe markdown renderer with raw HTML escaped and headings demoted one level; an empty body says the document is empty. |
| R4 | MUST | Each body heading gets an id of `doc-` plus a slug of its text, deduplicated with `-2`, `-3`, set through the renderer's attribute handling so heading text is escaped. |
| R5 | MUST | A side panel shows the ticket, type, created and updated, and an outline linking the top two heading levels the body itself uses to their ids (a heading with no words is anchored but not listed), the text taken from the heading's inline text with markup dropped rather than its source. That
text is plain and autoescaped by the template; only the body HTML is marked safe. |
| R6 | MUST | When the ticket has two or more documents, tabs list them in declared type order then title, on one line that scrolls sideways, the current one marked `aria-current="page"`; an "all" disclosure lists every document grouped by type with its date; the header shows "n of m". With one document there are none of these. |
| R7 | MUST | The current tab, the menu's current entry and the position are decided by the id knot answered with, so a prefix id marks the right one; links use full ids. |
| R8 | MUST | An unknown id, or a prefix knot refuses as ambiguous (`ambiguous_doc`), answers 404 with the page that offers the ticket list. The reading layer maps both codes to the missing-document refusal. |
| R10 | MUST | The declared test backlog resolves a document id as knot does: an exact id first, then a prefix matching exactly one document; a prefix matching several, or none, is the missing-document refusal. |
| R9 | MUST | A document whose ticket is closed renders the same; a document whose ticket knot cannot find renders with the bare ticket id and itself alone, not a 404. |

## Design

**Approach:** a `document` page method reads `document(id)`, then `documents(doc.ticket)` and
`ticket(doc.ticket)`, each of the last two catching `MissingTicket` locally. Documents are ordered
through `Project.ordered`. The body goes through a new renderer function returning the HTML and the
outline from one traversal. The template marks only that HTML safe, as the `prose` filter does.

**Interfaces and contracts:** the renderer function takes markdown text and returns HTML plus a
tuple of outline entries (level, text, anchor), the text plain. It and the existing `rendered`
share one token walk parameterised by demotion, so the ticket page's output is unchanged.

**Prior art to mirror:** the ticket page's `_parent_of` for the degradable read; `prose.rendered`
for the renderer; the ticket page's header and cards for layout; the mockup's tab strip, "all"
menu and side panel.

**Key decisions:** the "all" menu shows whenever there are tabs rather than only on overflow, so
it needs no script and the page renders the same everywhere; a small static script only scrolls the
current tab into view. Heading ids are prefixed so a document cannot collide with the page's own.
Three reads per page: the breadcrumb's title is worth a process, and it degrades.

## Acceptance Criteria

### Story 1: When I open a document, I want to read it with its context around it.

**AC-1** — Given a document with a body of headings, a list and a code span, when its page renders,
then the body is HTML with the headings demoted one level, and the breadcrumb, title, type, id and
last change are shown.
**AC-2** — Given a heading "Plan" twice and one containing `"><script>`, when the page renders,
then the ids are `doc-plan` and `doc-plan-2`, the script text is escaped, and the outline links
`#doc-plan` to the heading with that id.
**AC-3** — Given an unknown id, when the page is requested, then it answers 404 offering the ticket
list; given knot's `ambiguous_doc` for a prefix, the reading layer raises the same refusal.
**AC-4** — Given a document with an empty body, when the page renders, then it says the document is
empty.
**AC-5** — Given a document whose ticket knot cannot find, when the page renders, then it answers
200 with the body and the bare ticket id, and no "ticket called" text.
**AC-6** — Given a document on a closed ticket, when the page renders, then it answers 200 with its
tabs.

### Story 2: When a ticket has several documents, I want to move between them.

**AC-7** — Given a ticket with a plan and a spec, when the plan's page renders, then the tabs read
spec then plan, the plan's tab is marked current, and the header shows "2 of 2".
**AC-8** — Given the same ticket, when the page renders, then the "all" disclosure lists both
grouped under their types with dates.
**AC-9** — Given a prefix of the plan's id, when the page renders, then the plan's tab is still
the current one and the tabs link full ids.
**AC-10** — Given a ticket with one document, when its page renders, then there are no tabs, no
"all" menu and no position.

### Traceability
| Story AC | Spec ACs | Notes |
|----------|----------|-------|
| The body renders as safe markdown with the breadcrumb, meta and outline | AC-1, AC-2, AC-4 | |
| An unknown id answers 404 with the ticket list offered | AC-3 | |
| Tabs list the documents in type then title order, the current one marked | AC-7, AC-9 | |
| Overflowing tabs scroll on one line, and the all menu lists every document grouped by type | AC-8, AC-10 | the menu shows whenever there are tabs, not only on overflow; the one-line scroll is CSS |
| The page works for a document whose ticket is closed | AC-6, AC-5 | an orphan renders too |
| The route is a GET and the route-table test includes it | R1 | both route lists in `tests/panel/test_routes.py` gain it |

## Boundaries
- ✅ Always: mark safe only the renderer's own output; read only through the `Backlog` port.
- 🚫 Never: build heading markup as strings; enable raw HTML in the renderer; add a write verb;
  match or parse a document id in the panel. knot resolves a prefix, and the test double resolves
  it the same way.

## Testing Strategy
AC-2 and AC-4's rendering are unit tests of the renderer as well as page tests; every other AC is
a rendered-page test over a declared backlog. The sideways scroll and the scroll-into-view are
checked in a browser over a scratch project.

---
After implementing, compare results against each acceptance criterion above
and list any unmet requirements.
