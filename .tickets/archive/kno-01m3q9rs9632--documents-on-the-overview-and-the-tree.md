---
id: kno-01m3q9rs9632
title: Documents on the overview and the tree
status: closed
type: task
priority: 2
mode: afk
created: '2026-09-29T19:20:22.054405Z'
updated: '2026-09-29T22:45:40.633832Z'
closed: '2026-09-29T22:45:40.633832Z'
assignee: Jason Risch
parent: kno-01m3q9rmck1r
acceptance:
- title: The overview shows a documents card counting by type, with links to the filtered list, only when documents exist
  done: true
- title: Tree rows show owned types, and a dashed tag for a required type the ticket lacks
  done: true
- title: The footer shows the document count
  done: true
- title: Tag narrowing applies to the documents card like every other overview card
  done: true
deps:
- kno-01m3q9rpt69f
---

## Description

Show documents on the overview and the tree. Mockup: the "Overview and tree" screen at https://claude.ai/artifact/45uvLj8TfGTetvbob2nzEN.

## Design

- A `documents` card on the overview counting documents by type, each count linking to the tickets list filtered to that type. Absent when the project has no documents.
- Tree rows carry the same type tags as the lists. A required type the ticket lacks for its next status shows as a dashed tag.
- No card for tickets waiting on documents: that was tried in the mockup and dropped. Missing documents show on the ticket page, the tree and through the list filter.
- The footer adds the document count beside the live and archived counts.

## Notes

**2026-09-29T22:07:49.796545Z**

Starting work on this task.

**2026-09-29T22:45:38.532746Z**

Implementation artifacts attached
branch: jr/kno-01m3q9rmck1r-attached-documents commit: 5115e03fe91f50140de64c414edf323898b8f763
- Brainstorm: docs/ai-assistant-ideation/kno-01m3q9rs9632-overview-tree-documents-brainstorm.md @ 5115e03fe91f50140de64c414edf323898b8f763
- Spec: docs/ai-assistant-ideation/kno-01m3q9rs9632-overview-tree-documents-spec.md @ 5115e03fe91f50140de64c414edf323898b8f763
- Plan: docs/ai-assistant-ideation/kno-01m3q9rs9632-overview-tree-documents-plan.md @ 5115e03fe91f50140de64c414edf323898b8f763

**2026-09-29T22:45:39.135190Z**

Acceptance criteria ticked as verified: 1, 2, 3, 4

**2026-09-29T22:45:39.558937Z**

Task completed in 5115e03. The overview has a "by document" card: live tickets owning each declared type, tag-narrowed, each row linking to that type alone. It hides when none of its tickets owns a document. Tree rows show owned types and dashed missing ones through the macro the lists use. The footer counts the project's documents.

Two points differ from the ticket's wording. The card counts tickets per type, not documents, because knot's listings name types without counting them; the count then equals its list. The mockup's document counts are not delivered as drawn. And "a required type the ticket lacks for its next status" is every status that gates it, as the lists show, since knot's statuses are a vocabulary with no next.

The tree's lists now show dashes as its rows do, which supersedes story kno-01m3q9rr1aer's AC-2 for the tree. That story's test was rewritten to match. query_string now refuses a document type change, pointing to having().

Filed kno-01m3qneqctfh: on /?closed=1 every overview card's count can disagree with its link. This predates the story.

Reviewed: brainstorm by the quality engineer (two rounds), spec and plan by their reviewers and the solution architect's gates, implementation by the quality engineer and the adversarial verifier. No P0 or P1 remained.
