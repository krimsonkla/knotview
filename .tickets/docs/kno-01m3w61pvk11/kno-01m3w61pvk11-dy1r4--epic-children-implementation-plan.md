---
id: kno-01m3w61pvk11-dy1r4
ticket: kno-01m3w61pvk11
title: Epic children implementation plan
type: plan
created: '2026-10-01T17:01:32.153103Z'
updated: '2026-10-01T17:01:32.153103Z'
---

# Epic children implementation plan

**Spec:** `kno-01m3w61pvk11-epic-children-spec.md`. **Test route:** strict.

## Task 1: Tests (tests/panel/test_ticket_children.py)
- [ ] A declared backlog built in the file: an epic with children in mixed statuses, one missing
  reference and one undeclared status; AC-1 to AC-8 as rendered-page tests.

## Task 2: Ordering and filtering
- [ ] `Project.by_status(references)`: stable sort on (declared index, else len(statuses);
  missing last). Unit test in tests/values/test_project.py.
- [ ] `Pages.ticket`: read `children` from the query (only `live` hides); compute
  `children = project.by_status(ticket.children)`, `shown` (filtered when hiding),
  `closed_count`, and `siblings = project.by_status(parent.children minus this ticket)`; pass
  them to the template.

## Task 3: Template
- [ ] Pull children out of the graph loop's tuple only as far as its references: the loop entry
  becomes ("children", shown, ()), and the card shows when `references or extras or hidden`.
  The heading's number and toggle come from passed values; the toggle links `?children=live` or
  the bare page.
- [ ] The siblings card loops `siblings` and counts `siblings | length`.

## Task 4: Gate
- [ ] pytest, ruff, black, pylint, prek; browser check on an epic; /code-review high until approved.
