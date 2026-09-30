---
id: kno-01m3q9rtgqa9
title: Documents on the ticket page, and missing ones in blocked by
status: closed
type: task
priority: 2
mode: afk
created: '2026-09-29T19:20:23.319495Z'
updated: '2026-09-30T00:12:44.941537Z'
closed: '2026-09-30T00:12:44.941537Z'
assignee: Jason Risch
parent: kno-01m3q9rmck1r
acceptance:
- title: The documents card lists every document with type, title, id and last change, above acceptance
  done: true
- title: Rows order by the project's type order, then title
  done: true
- title: A missing required type appears as a quiet row in blocked by and counts toward its number
  done: true
- title: A ticket with no documents and no missing types shows neither
  done: true
deps:
- kno-01m3q9rpt69f
- kno-01m3q9rvrdst
---

## Description

Show a ticket's documents on its page, and show a missing required document as something that blocks it. Mockup: the "Ticket page" screen at https://claude.ai/artifact/45uvLj8TfGTetvbob2nzEN.

## Design

- A `documents` card right after the header, above acceptance, since a spec or plan is often why someone opens a ticket. Each row: type tag, title linking to the document page, id, and the last change. Created and updated come from `document list`, one extra read per ticket page. Rows order by type as `.knot.edn` lists them, then by title. No card when the ticket owns none.
- A required type the ticket lacks for its next status is a row in the existing "blocked by" card, beside the blocking tickets: a dashed type tag, "no plan attached", and a muted note naming the status it gates. It counts toward the card's number. No banner and no command hint.
- The header gains a chip with the document count.

## Notes

**2026-09-29T23:51:06.620845Z**

Starting work on this task.

**2026-09-30T00:12:42.468195Z**

Implementation artifacts attached
branch: jr/kno-01m3q9rmck1r-attached-documents commit: 53915aaeb884e5ff1e5904d71aaeb6a2d4e92a54
- Brainstorm: docs/ai-assistant-ideation/kno-01m3q9rtgqa9-ticket-documents-brainstorm.md @ 53915aaeb884e5ff1e5904d71aaeb6a2d4e92a54
- Spec: docs/ai-assistant-ideation/kno-01m3q9rtgqa9-ticket-documents-spec.md @ 53915aaeb884e5ff1e5904d71aaeb6a2d4e92a54
- Plan: docs/ai-assistant-ideation/kno-01m3q9rtgqa9-ticket-documents-plan.md @ 53915aaeb884e5ff1e5904d71aaeb6a2d4e92a54

**2026-09-30T00:12:43.837273Z**

Acceptance criteria ticked as verified: 1, 2, 3, 4

**2026-09-30T00:12:44.269952Z**

Task completed in 53915aa. The ticket page now opens with a documents card, above acceptance: type, title linking to the document page, id and last change, in declared type order. A header chip counts the documents and links to the card. If knot refuses the document list, the card draws the documents show stated, without times.

For a live ticket, each missing required type is a quiet row in "blocked by": a dashed tag, "no <type> attached", and "needed to enter" naming every status that needs it. These rows count toward the card's number, whose tooltip says what it counts. The word "missing" stays with blocker ids that name no ticket.

Two points differ from the ticket's wording:
- "for its next status" is every status that gates it, since knot's statuses have no order.
- The card's number was already a count of its rows, closed and unknown blockers included, unlike the lists' open-blocker column.

Also in this story:
- Project.is_live is now the one live test the lists, the filter and this page share.
- The lists' dashed tooltip names every status.
- Filed kno-01m3qtd4ax4g: knot reads a misfiled document differently in listings and in show.

Reviewed: brainstorm by the quality engineer (two rounds), spec and plan by their reviewers and the solution architect's gates, and implementation by the quality engineer and the adversarial verifier. No P0 or P1 remained.
