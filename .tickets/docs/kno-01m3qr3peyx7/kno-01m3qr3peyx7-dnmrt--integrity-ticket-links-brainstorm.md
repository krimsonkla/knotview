---
id: kno-01m3qr3peyx7-dnmrt
ticket: kno-01m3qr3peyx7
title: Integrity ticket links brainstorm
type: other
created: '2026-09-30T04:21:08.107425Z'
updated: '2026-09-30T04:21:08.107425Z'
---

# Integrity ticket links brainstorm

Story: kno-01m3qr3peyx7, "Link ticket ids on the integrity card". Date: 2026-09-30. Mode:
teams-equivalent, quality-engineer challenger.

## Problem

The integrity card links document ids for four verified codes and shows every other issue as
plain text, though most of knot's issues are about a ticket the reader would want to open.

## Survey

From knot 0.15.0's check.clj. `:ids` names the records an issue is about; the offending value
lives in `:field` and `:value`.

- **Ticket ids:** invalid_status, invalid_type, invalid_mode, invalid_priority,
  terminal_outside_archive, unknown_id (the holder), acceptance_invalid, legacy_acceptance_section,
  reserved_section, duplicate_section, legacy_documents_section, dep_cycle (every ticket on the
  cycle, the first repeated), missing_required_field (ticket arm [id] or []; document arm []).
- **Document ids, already linked:** invalid_doc_type, doc_directory_mismatch,
  doc_id_owner_mismatch, doc_unknown_ticket.
- **Plain:** duplicate_doc_id (ambiguous). **Always empty:** unreachable_documents,
  invalid_active_status, skill_stale, frontmatter_parse_error.
- knot emits `ids: [null]` for invalid_priority and terminal_outside_archive on a ticket with no id,
  against its own contract.

## Approach

Issue gains `ticket_ids` for the verified ticket codes, deduplicated in order. One guard keeps only
non-empty string ids for the text and both kinds of link, so a null id is neither linked nor
written as "None". The card links ticket ids ahead of the text as it does document ids.

## What the challenger changed

The null-id guard (measured against knot); missing_required_field's two tiers named; the always-
empty codes asserted to be in neither set; dep_cycle's dedupe explained; whole-item and empty-ids
tests.
