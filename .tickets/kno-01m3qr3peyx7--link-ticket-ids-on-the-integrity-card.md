---
id: kno-01m3qr3peyx7
title: Link ticket ids on the integrity card
status: open
type: task
priority: 2
mode: afk
created: '2026-09-29T23:30:59.678203Z'
updated: '2026-09-29T23:30:59.793920Z'
assignee: ''
---

The overview's integrity card links document ids for the four document issue codes verified in kno-01m3q9rx099f, and shows every other issue as plain text. Ticket ids in the other codes (unknown_id, the cycle codes, legacy_documents_section, and the rest) could link to their ticket pages too.

## Design

Verify each code's `ids` against knot's output one at a time, as kno-01m3q9rx099f did for documents. A code's name is not a contract: legacy_documents_section, for one, names a ticket. Link only the verified codes; everything else stays plain.