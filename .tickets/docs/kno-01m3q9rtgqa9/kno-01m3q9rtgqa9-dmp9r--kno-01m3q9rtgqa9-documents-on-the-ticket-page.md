---
id: kno-01m3q9rtgqa9-dmp9r
ticket: kno-01m3q9rtgqa9
title: Documents on the ticket page implementation plan
type: plan
created: '2026-09-30T00:08:59.128600Z'
updated: '2026-09-30T00:09:27.825871Z'
---

# kno-01m3q9rtgqa9 — Documents on the ticket page implementation plan

**Goal:** a ticket's page shows its documents first and shows a missing required document with its
blockers.

**Architecture:** `Project.missing_by_type(ticket)` groups `missing_documents` by type in declared order,
with every status needing each. `Pages.ticket` reads `documents(ticket.id)`, falling back on
`UnreadableBacklog` to `ticket.documents`, ordered by `Project.ordered`, and passes `documents` and
`missing_types` (empty unless `Project.is_live`, the one live test the lists, the filter and this page share). `ticket.html` draws the card, the chip and the rows.
`_documents.html` titles its dashed tags from `lacking`. Spec:
`kno-01m3q9rtgqa9-ticket-documents-spec.md`.

**Tech stack:** FastAPI, Jinja2, pytest over a declared backlog. **Test route:** strict.

## Coverage

| Spec item | Task |
|-----------|------|
| R3 (grouping), AC-5 | 1 |
| R1, R2, R5, R6, AC-1, AC-2, AC-3 | 2 |
| R3, R4, AC-4, AC-6, AC-7 | 3 |

## Files

- Modify: `values/project.py`, `panel/app.py`, `templates/ticket.html`,
  `templates/_documents.html`, `static/panel.css` (the missing row's layout),
  `tests/panel/declared.py` (a declared backlog whose document list refuses)
- Create: `tests/panel/test_ticket_documents.py`
- Modify tests: `tests/values/test_project.py` (missing_by_type, is_live), `tests/panel/test_list_documents.py` (the
  widened title keeps its single-status assertion)

## Task 1: Project.missing_by_type

- [ ] **Failing tests** in `tests/values/test_project.py`, for a project requiring spec and plan
  for in_progress and spec for review:
  - a ticket owning nothing lacks `(("spec", ("in_progress", "review")), ("plan", ("in_progress",)))`;
  - a ticket owning a spec lacks only the plan;
  - a ticket owning both lacks nothing.
- [ ] `missing_by_type(ticket) -> tuple[tuple[str, tuple[str, ...]], ...]`: walk `missing_documents`,
  collect the statuses per type, and return them in `ordered_types` order.
- [ ] `_documents.html`: iterate `project.missing_by_type(ticket)`, with the title "needed to enter
  {{ statuses | join(', ') }}". The `drawn` namespace accumulator is deleted, since grouping replaces it.

## Task 2: The card and the chip

- [ ] `DeclaredBacklog` gains `documents_refused: bool = False`. When it is set, `documents()` raises
  `UnreadableBacklog("refused", advice="", code="invalid_argument")`, a refusal `_parent_of`'s
  narrower catch would not swallow.
- [ ] **Failing render tests** in `test_ticket_documents.py` over `PARENT` with `PARENT_DOCUMENTS`:
  - AC-1: `id="documents"` precedes the acceptance card; spec's row precedes plan's; each row has
    the doctype span, a link to `/document/<id>`, the id and `updated <time`; the header has
    `href="#documents"` with "2 documents";
  - AC-2: with `documents_refused`, the page is 200 with both titles and no `updated <time` in
    the card;
  - AC-3: `ORPHAN`'s page has no `id="documents"` and no " documents<".
- [ ] `Pages.ticket`: add `documents=self._documents_of(ticket, project)`, where `_documents_of`
  tries `backlog.documents(ticket.id)` and on `UnreadableBacklog` uses `ticket.documents`, then
  applies `project.ordered`. Add `lacking=()` when `ticket.status` is terminal, else
  `project.missing_by_type(ticket)`.
- [ ] `ticket.html`:
  - after `</header>` and before acceptance, when `documents`, add
    `<section class="card" id="documents">` holding h2 "documents" with the count, then
    `<ul class="refs">` with rows: the doctype span, the title link, the id span, and
    `{% if one.updated %}<span class="muted">updated {{ stamp(one.updated) }}</span>{% endif %}`;
  - in the header meta, when `documents`,
    `<a class="chip" href="#documents">{{ documents | length }} documents</a>`.

## Task 3: Missing rows in "blocked by"

- [ ] **Failing render tests** over a project whose `required_docs` is
  `(("in_progress", ("spec", "plan")), ("review", ("spec",)))`, plus a `review` status:
  - AC-4: `CHILD` (in_progress, owning nothing) shows "blocked by", counting 2 blockers plus 2
    types (`<span class="num">4</span>`), a `doctype missing` spec row and "no spec attached";
  - AC-5: the spec row names "needed to enter in_progress, review";
  - AC-6: a closed ticket has no "no spec attached";
  - AC-7: `ORPHAN` under `PROJECT` (no requirements) has no "blocked by", and no document row
    contains `chip muted">missing`.
- [ ] `ticket.html`: the loop's tuples gain a third element:
  `("blocked by", ticket.blockers, lacking)`, `("blocking", ticket.blocking, ())`,
  `("children", ticket.children, ())` and `("linked", ticket.linked, ())`. A card shows when
  `references or extras`. The h2 count is `references | length + extras | length`, titled "rows in
  this card: tickets, and missing documents where shown". After the reference rows, each extra is
  `<li class="lacking"><span class="doctype missing">{{ kind }}</span> no {{ kind }} attached <span class="muted">needed to enter {{ statuses | join(", ") }}</span></li>`.

## Task 4: Gate

- [ ] `black`, `pytest` (100 percent), `ruff`, `pylint`, and `prek run --files <changed>` and
  `--all-files`.
- [ ] Browser check over a scratch project against the mockup's ticket screen.
