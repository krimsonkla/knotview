---
id: kno-01m3q9rr1aer
title: Documents in every ticket list, with a multi-select filter
status: closed
type: task
priority: 2
mode: afk
created: '2026-09-29T19:20:20.778166Z'
updated: '2026-09-29T22:45:39.973692Z'
closed: '2026-09-29T22:05:36.664781Z'
assignee: Jason Risch
parent: kno-01m3q9rmck1r
acceptance:
- title: Every ticket table shows a docs column with one tag per owned type, linking to the document
  done: true
- title: The column hides when no row owns a document
  done: true
- title: The documents filter accepts several types and keeps tickets owning all of them
  done: true
- title: '"none attached" and "missing a required type" filter as described, and "none attached" clears ticked types'
  done: true
- title: Each ticked value is a removable chip, and the filtered view round-trips through its URL
  done: true
deps:
- kno-01m3q9rpt69f
---

## Description

Show which documents each ticket owns in every ticket table, and let a reader filter by them. Mockup: the "Every ticket list" screen at https://claude.ai/artifact/45uvLj8TfGTetvbob2nzEN.

## Design

- A `docs` column after the title in `_ticket_table.html`, one small tag per type the ticket owns, each linking to the ticket page's documents card (`/ticket/<id>#documents`). A listing row carries only type names, never document ids, and a ticket can own several documents of one type, so a tag cannot name one document. Empty for a ticket with none. The column hides when every row is empty, as the assignee column does. The queues and overview cards share the table, so they gain it too.
- A `documents` filter on the tickets page: a multi-select built as a native disclosure of checkboxes, so it works without script. Each tick is a repeated query value, `?doc=spec&doc=plan`.
- Ticking several types keeps tickets that own all of them, matching the tag filter. Below the types, "none attached" and "missing a required type" are separate ticks; "none attached" clears the types.
- Each ticked value is its own removable chip in the summary line, like the other filter chips.

## Notes

**2026-09-29T21:34:49.492926Z**

Starting work on this task.

**2026-09-29T22:04:05.779658Z**

Implementation artifacts attached
branch: jr/kno-01m3q9rmck1r-attached-documents commit: 1b97d98be6444c7fee52dd552615beda9e028052
- Brainstorm: docs/ai-assistant-ideation/kno-01m3q9rr1aer-list-documents-brainstorm.md @ 1b97d98be6444c7fee52dd552615beda9e028052
- Spec: docs/ai-assistant-ideation/kno-01m3q9rr1aer-list-documents-spec.md @ 1b97d98be6444c7fee52dd552615beda9e028052
- Plan: docs/ai-assistant-ideation/kno-01m3q9rr1aer-list-documents-plan.md @ 1b97d98be6444c7fee52dd552615beda9e028052

**2026-09-29T22:05:34.493086Z**

Acceptance criteria ticked as verified: 1, 2, 3, 4, 5

**2026-09-29T22:05:35.369493Z**

Task completed in 1b97d98. Every ticket table has a docs column of owned types; the tickets page and both queues show a live ticket's missing required types dashed; the tickets page filters by ticked types (all must be owned), none attached, and missing a required type, each a chip that drops only itself.

The first criterion is delivered as a link to the ticket's documents card rather than to one document, per the amended design: a listing row carries type names only, and a ticket may own several documents of one type. The documents card and its anchor arrive with the ticket-page story.

Also fixed here: the assignee header sat before lev while every row drew the cell after lvl; the empty row now spans every column; links the templates built by hand (type, status, tag, assignee, component, mode) are now percent-encoded, so a tag like r&d no longer truncates; and "missing a required type" is neither offered nor applied on a project with no required documents.

Reviewed by the quality engineer and the adversarial verifier, cycle 1, no P0 or P1; four P2s fixed in place.

**2026-09-29T22:45:39.973692Z**

The tree's stray and orphan lists now show dashed missing types, as the tree's rows do: kno-01m3q9rs9632 superseded this story's AC-2 for the tree, in 5115e03. The overview cards are unchanged.
