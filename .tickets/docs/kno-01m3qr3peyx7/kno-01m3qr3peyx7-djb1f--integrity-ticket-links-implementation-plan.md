---
id: kno-01m3qr3peyx7-djb1f
ticket: kno-01m3qr3peyx7
title: Integrity ticket links implementation plan
type: plan
created: '2026-09-30T04:21:08.464447Z'
updated: '2026-09-30T04:21:08.464447Z'
---

# Integrity ticket links implementation plan

**Spec:** `kno-01m3qr3peyx7-ticket-links-spec.md`. **Test route:** strict.

## Task 1: Reading
- [ ] Failing tests in tests/reading/test_issues.py: one per ticket code (parametrized) linking
  its id; dep_cycle deduplicated; `[null]` guarded; disjoint sets and the plain codes in neither;
  unknown_id's target not linked.
- [ ] `Issue.ticket_ids: tuple[str, ...] = ()`; `Issue.found(..., ticket_ids=())`.
- [ ] knot_command.py: `TICKET_CODES` with the survey's comment; `_named(ids)` keeping non-empty
  strings in order, deduplicated; `_described` uses it for the head; `_issue` fills document or
  ticket ids by code and leaves the head off when it links.

## Task 2: Card
- [ ] Failing render tests in tests/panel/test_overview.py: an unknown_id item links
  `/ticket/<id>`; a four-ticket cycle's whole `<li>`; frontmatter_parse_error shows its path.
- [ ] overview.html: ticket links before the document links, through the `segment` filter.

## Task 3: Recorded and real
- [ ] The recorded check-issues' unknown_id reads as a ticket link; test_real_knot asserts the same.

## Task 4: Gate
- [ ] pytest, ruff, black, pylint, prek; /code-review high until approved.
