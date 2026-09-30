---
id: kno-01m3q9rx099f
title: Live reload and integrity issues for documents
status: closed
type: task
priority: 2
mode: afk
created: '2026-09-29T19:20:25.865416Z'
updated: '2026-09-29T23:49:32.303087Z'
closed: '2026-09-29T23:49:32.303087Z'
assignee: Jason Risch
parent: kno-01m3q9rmck1r
acceptance:
- title: A change to a document under a custom :docs-dir outside the tickets directory moves the digest
  done: true
- title: Document issues from knot check render on the integrity card with their path
  done: true
deps:
- kno-01m3q9rpt69f
---

## Description

Two edges of documents outside the pages themselves. The live stream's digest walks every markdown file under the tickets directory, so documents in the default place already trigger a reload, but a project that sets `:docs-dir` outside the tickets directory would not reload on a document change. And `knot check` now reports document issues (`doc_unknown_ticket`, `invalid_doc_type`, `doc_directory_mismatch`, `doc_id_owner_mismatch`, `duplicate_doc_id`, `unreachable_documents`, `legacy_documents_section`) whose `path` points at a document rather than a ticket.

## Design

The digest also walks `info`'s `docs_path` when it lies outside the tickets directory. The integrity card shows document issues with their path, and links the document when its id is known.

## Notes

**2026-09-29T23:26:50.464Z**

Starting work on this task.

**2026-09-29T23:48:34.576063Z**

Implementation artifacts attached
branch: jr/kno-01m3q9rmck1r-attached-documents commit: 9a142f0239262d1b877cf0dd6f0daa80d52340ed
- Brainstorm: docs/ai-assistant-ideation/kno-01m3q9rx099f-docs-live-integrity-brainstorm.md @ 9a142f0239262d1b877cf0dd6f0daa80d52340ed
- Spec: docs/ai-assistant-ideation/kno-01m3q9rx099f-docs-live-integrity-spec.md @ 9a142f0239262d1b877cf0dd6f0daa80d52340ed
- Plan: docs/ai-assistant-ideation/kno-01m3q9rx099f-docs-live-integrity-plan.md @ 9a142f0239262d1b877cf0dd6f0daa80d52340ed

**2026-09-29T23:49:18.481109Z**

Implementation artifacts attached
branch: jr/kno-01m3q9rmck1r-attached-documents commit: 53471dbe0d46c8b79d96e16d5f66c104bc2666a3
- Brainstorm: docs/ai-assistant-ideation/kno-01m3q9rx099f-docs-live-integrity-brainstorm.md @ 53471dbe0d46c8b79d96e16d5f66c104bc2666a3
- Spec: docs/ai-assistant-ideation/kno-01m3q9rx099f-docs-live-integrity-spec.md @ 53471dbe0d46c8b79d96e16d5f66c104bc2666a3
- Plan: docs/ai-assistant-ideation/kno-01m3q9rx099f-docs-live-integrity-plan.md @ 53471dbe0d46c8b79d96e16d5f66c104bc2666a3

**2026-09-29T23:49:18.946329Z**

The artifacts note before this one pinned 9a142f0, from a commit attempt a hook refused; the docs are in 53471db, which the note above pins.

**2026-09-29T23:49:31.137782Z**

Acceptance criteria ticked as verified: 1, 2

**2026-09-29T23:49:31.580395Z**

Task completed in 53471db. When .knot.edn's :docs-dir puts documents outside the tickets directory, the digest now walks that directory as well. The default layout still has a single walk. Checked against real knot: editing a document outside .tickets pushed a changed event on /live.

The integrity card shows each document issue's path from the project root, with the full path on hover. Issues with the four document codes checked against knot 0.15 (doc_unknown_ticket, invalid_doc_type, doc_directory_mismatch, doc_id_owner_mismatch) link to the documents they name. Every other code stays plain text. duplicate_doc_id names an id knot refuses as ambiguous, and legacy_documents_section names a ticket, so neither links.

Follow-ups:
- Filed kno-01m3qr3peyx7 to link ticket ids the same way.
- Noted on kno-01m3qdwrjdbx that no committed recording holds a check issue carrying a path.

Reviewed: brainstorm by the quality engineer (two rounds), spec and plan by their reviewers and the solution architect's gates, and implementation by the quality engineer and the adversarial verifier. No P0 or P1 remained, and every P2 was fixed.
