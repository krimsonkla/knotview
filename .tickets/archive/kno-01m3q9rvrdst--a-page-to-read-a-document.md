---
id: kno-01m3q9rvrdst
title: A page to read a document
status: closed
type: task
priority: 2
mode: afk
created: '2026-09-29T19:20:24.589470Z'
updated: '2026-09-29T23:25:21.614544Z'
closed: '2026-09-29T23:25:21.614544Z'
assignee: Jason Risch
parent: kno-01m3q9rmck1r
acceptance:
- title: /document/<id> renders the body as safe markdown with the breadcrumb, meta and outline
  done: true
- title: An unknown id answers 404 with the ticket list offered
  done: true
- title: Tabs list the ticket's documents in type then title order, with the current one marked
  done: true
- title: Overflowing tabs scroll on one line, and the all menu lists every document grouped by type
  done: true
- title: The page works for a document whose ticket is closed
  done: true
- title: The route is a GET and the route-table test includes it
  done: true
deps:
- kno-01m3q9rpt69f
---

## Description

Add a page to read one document. Mockup: the "Document page" screen at https://claude.ai/artifact/45uvLj8TfGTetvbob2nzEN.

## Design

- A read-only route `/document/<id>`, read with `knot document show`. An unknown id is a 404 offering the ticket list, as a missing ticket is.
- The body renders as markdown through the existing safe `prose` renderer, headings demoted so the page keeps one title.
- A breadcrumb back to the owning ticket, the title, a type tag, the id and the last change.
- Tabs across the top switch between the ticket's other documents, ordered by type then title. When they do not fit, the row stays on one line, scrolls sideways and fades at the edge, and opens scrolled to the current tab. An "all" menu at the end lists every document grouped by type with its date; it shows only when the tabs overflow and is a native disclosure. The header shows the position, such as "4 of 9".
- A side panel with the owner, type, created and updated, and an outline built from the document's headings.
- Works the same for a closed ticket's documents.

## Notes

**2026-09-29T22:47:03.423719Z**

Starting work on this task.

**2026-09-29T23:25:07.917073Z**

Implementation artifacts attached
branch: jr/kno-01m3q9rmck1r-attached-documents commit: af5e1ec8c71199a8b3fd73a6ae45616cb8c5bc4e
- Brainstorm: docs/ai-assistant-ideation/kno-01m3q9rvrdst-document-page-brainstorm.md @ af5e1ec8c71199a8b3fd73a6ae45616cb8c5bc4e
- Spec: docs/ai-assistant-ideation/kno-01m3q9rvrdst-document-page-spec.md @ af5e1ec8c71199a8b3fd73a6ae45616cb8c5bc4e
- Plan: docs/ai-assistant-ideation/kno-01m3q9rvrdst-document-page-plan.md @ af5e1ec8c71199a8b3fd73a6ae45616cb8c5bc4e

**2026-09-29T23:25:20.659119Z**

Acceptance criteria ticked as verified: 1, 2, 3, 4, 5, 6

**2026-09-29T23:25:21.026989Z**

Task completed in af5e1ec. /document/<id> reads the document through knot's document show. It shows a breadcrumb to the ticket, the title, type, id and last change, and the body as safe markdown with anchored headings. A side panel holds the ticket, type, times and an outline of the top two heading levels the document uses.

Two deviations from the ticket's design:
- The "all" menu shows whenever a ticket has two or more documents, not only when the tabs overflow. That way the page works the same without script and can be tested. A small script only scrolls the current tab into view.
- A ticket with one document shows no tabs, no menu and no position. The third criterion's "tabs list the ticket's documents" applies from two documents up.

Also in this story:
- knot answers ambiguous_doc for a prefix several documents share, and the panel treats it as a 404, like an unknown id.
- A document whose ticket knot cannot find still renders, with the bare ticket id.
- Ids in the page's links are encoded as one path segment.
- The test backlog now resolves document prefixes the way knot does, within one ticket's documents.

Reviewed: brainstorm by the quality engineer (two rounds), spec and plan by their reviewers and the solution architect's gates, and implementation by the quality engineer and the adversarial verifier. No P0 or P1 remained, and every P2 was fixed. Checked over real knot with nine documents on one ticket at desktop and phone width.
