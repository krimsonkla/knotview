---
id: kno-01m3qr3peyx7-dsdf2
ticket: kno-01m3qr3peyx7
title: Integrity ticket links design spec
type: spec
created: '2026-09-30T04:21:08.285111Z'
updated: '2026-09-30T04:21:08.285111Z'
---

# Integrity ticket links design spec

**Story:** Link ticket ids on the integrity card (kno-01m3qr3peyx7)
**Tier:** Small — one value, one reader function, one template block

## Requirements

| ID | Priority | Requirement |
|----|----------|-------------|
| R1 | MUST | An issue of a verified ticket code (`TICKET_CODES` in reading/knot_command.py is the source of truth, citing knot 0.15.0's check.clj, as `LINKED` is for documents) carries its ids, deduplicated in order, as ticket ids; the card links each to `/ticket/<id>` ahead of the text, which omits them. |
| R2 | MUST | Only non-empty string ids are read, for the text and both kinds of link; a null id is neither linked nor written. |
| R3 | MUST | Document codes keep their document links; duplicate_doc_id and every code always carrying empty ids stay plain; the two sets are disjoint. |
| R4 | MUST | The code cites knot 0.15.0's check.clj and names missing_required_field as the first code to re-verify on a knot upgrade: it is the one code whose id kind depends on which tier emitted it, and if the document tier ever filled its ids, a document id would be linked to a ticket page. |
| R5 | MUST | Every code in a committed check recording is classified: in `TICKET_CODES`, in `LINKED`, or in the surveyed set of codes deliberately linked by neither. |

## Acceptance Criteria

**AC-1** — Given an unknown_id issue on a ticket, when the card renders, then the holder links to
its ticket page and the missing target stays in the message, unlinked.
**AC-2** — Given a dep_cycle over a, b, c, a, when read, then it links a, b and c once each, and the
whole list item reads the links then the message.
**AC-3** — Given `ids: [null]` on invalid_priority, when read, then there is no link and the text
has no "None".
**AC-4** — Given duplicate_doc_id or any always-empty code, when read, then nothing is linked.
**AC-5** — Given frontmatter_parse_error with a path and no ids, when the card renders, then the path
shows and nothing links.
**AC-6** — Given the recorded check-issues, when read, then its unknown_id holder is a ticket link;
the real-knot test asserts the same.
**AC-7** — Given the committed check recordings, when every issue's code is looked up, then each is
in one of the three classified sets, so a code knot renames or adds fails a test.
