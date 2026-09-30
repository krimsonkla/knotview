---
id: kno-01m3qr3peyx7
title: Link ticket ids on the integrity card
status: closed
type: task
priority: 2
mode: afk
created: '2026-09-29T23:30:59.678203Z'
updated: '2026-09-30T04:21:25.575087Z'
closed: '2026-09-30T04:21:25.575087Z'
assignee: Jason Risch
---

The overview's integrity card links document ids for the four document issue codes verified in kno-01m3q9rx099f, and shows every other issue as plain text. Ticket ids in the other codes (unknown_id, the cycle codes, legacy_documents_section, and the rest) could link to their ticket pages too.

## Design

Verify each code's `ids` against knot's output one at a time, as kno-01m3q9rx099f did for documents. A code's name is not a contract: legacy_documents_section, for one, names a ticket. Link only the verified codes; everything else stays plain.

## Notes

**2026-09-30T04:07:03.492227Z**

Starting work on this task.

**2026-09-30T04:21:24.569167Z**

Done in 52f7084 and c289bdb.

Thirteen check codes name tickets in their ids, surveyed from knot 0.15.0's check.clj: invalid_status, invalid_type, invalid_mode, invalid_priority, terminal_outside_archive, unknown_id (its holder), acceptance_invalid, legacy_acceptance_section, reserved_section, duplicate_section, legacy_documents_section, missing_required_field and dep_cycle. On the integrity card each such issue links its tickets, once each, ahead of its text. Document codes keep their document links. duplicate_doc_id and the codes whose ids are always empty stay plain.

Ids that are null or empty are neither linked nor written. knot emits `ids: [null]` for a ticket with no id, so the card no longer says "None". A test fails on any code in a committed check recording that has not been classified.

Reviewed:
- brainstorm by the quality engineer (two rounds);
- spec (clean) and plan by their reviewers and the solution architect;
- /code-review high twice with no findings, each run against real knot projects with every linked page returning 200.

The second review found a separate, pre-existing bug: a live ticket with no id makes the listings, and so every page, 503. Filed separately.
