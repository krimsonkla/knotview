---
id: kno-01m3q9rr1aer-df9j3
ticket: kno-01m3q9rr1aer
title: Documents in the lists implementation plan
type: plan
created: '2026-09-30T00:08:58.318402Z'
updated: '2026-09-30T00:09:26.326630Z'
---

# kno-01m3q9rr1aer — Documents in the lists implementation plan

**Goal:** every ticket table shows owned document types, and the tickets page filters by them.

**Architecture:** `Selection` gains `docs`, `undocumented` and `lacking`, read from a multi-valued
query; `matches` takes the project; `chips()` yields each applied filter with the query that drops
only it; `query_string` repeats `doc` and percent-encodes. `_ticket_table.html` draws the column
from `project.types_of` and, when the including page sets `show_missing`, dashed tags from
`project.missing_documents` for live tickets. Spec: `kno-01m3q9rr1aer-list-documents-spec.md`.

**Tech stack:** FastAPI, Jinja2, pytest over the TestClient and a declared backlog.

---

## Files

- Modify: `src/knotview/panel/selection.py`, `src/knotview/panel/app.py` (tickets page),
  `src/knotview/panel/templates/_ticket_table.html`, `templates/tickets.html`,
  `src/knotview/panel/static/panel.css` (the dashed tag)
- Modify tests: `tests/panel/test_tickets.py` (the two `matches` calls take the project; new
  tests), `tests/panel/declared.py` only if a declared ticket needs a document for a render test
- Create: `tests/panel/test_list_documents.py`

## Task 1: Selection

- [ ] **Failing unit tests** in `tests/panel/test_list_documents.py`: `asked` over a query with
  `doc` twice keeps declared types in declared order and drops an undeclared one; `nodocs=1`
  empties `docs`; `matches` with the project for owned-all, none, and lacking (live only);
  `chips()` for two types and both booleans, each chip's query dropping only itself and the rest
  surviving; `query_string` repeats `doc` and encodes `a b&c` as `a%20b%26c`.
- [ ] `asked(project, given, docs=())`: `docs` are the repeated values; keep those in
  `project.doc_types`, ordered by it; `undocumented` from `nodocs`, and when set, `docs=()`;
  `lacking` from `lacking`. The caller passes `request.query_params.getlist("doc")`.
- [ ] `matches(ticket, project)`: owned `set(project.types_of(ticket))` covers every selected type;
  `undocumented` needs no owned type; `lacking` needs a live ticket (status not terminal) with
  `project.missing_documents(ticket)` non-empty. Existing fields unchanged.
- [ ] `_set()` gains one entry per type `("has " + type, "doc", type)`, then `("none attached",
  "nodocs", "")` and `("missing a required type", "lacking", "")`. `chips()` returns (label,
  value, query without that entry). `without(label)` stays, now resolving through `chips()`;
  `applied()` becomes a view over `chips()` and `filtering` reads it, so the applied filters are
  written once.
- [ ] `query_string`: list of (field, value) pairs; `doc` once per type; `nodocs=1`, `lacking=1`;
  every value through `urllib.parse.quote(value, safe="")`.
- [ ] Update the two `matches` calls in `tests/panel/test_tickets.py` to pass `PROJECT`.

## Task 2: The table and the page

- [ ] **Failing render tests**: AC-1 (a row's tags spec then plan, linking to
  `/ticket/<id>#documents`); AC-2 (an overview card with a lacking ticket shows no dashed tag; the ready queue does); AC-3 (the
  column absent without owned or missing types and no filter, present with `nodocs=1`); AC-4 to
  AC-7 through `/tickets?...` over a declared backlog whose project requires spec and plan for
  in_progress; AC-8 chip links; AC-9 an encoded tag link.
- [ ] `_ticket_table.html`: compute `show_docs` = any row with owned types, or (when
  `show_missing`) any live row with missing types, or a documents filter applied. Header `docs`
  after title; the cell renders `project.types_of(ticket)` as `a.doctype` tags and, when
  `show_missing` and the ticket is live, each missing type of `project.missing_documents(ticket)`
  once, as `span.doctype.missing` titled "needed to enter <status>".
- [ ] `tickets.html` before its include, and `queue.html` once at the top of `block main` (it
  includes inside the waves loop and in the else branch): `{% set show_missing = true %}`; the
  partial defaults it to false; the documents
  disclosure with the checkboxes; the chip loop over `selection.chips()`.
- [ ] `app.py`: `Selection.asked(project, dict(request.query_params),
  docs=request.query_params.getlist("doc"))` at both call sites, the overview and the tickets
  page; the bare `Selection()` in the 404 handler stays; `selection.matches(one,
  project)` on the tickets page.
- [ ] `panel.css`: `.doctype` and `.doctype.missing` (dashed border, faint text), using the
  existing tokens.

## Task 3: Gate

- [ ] `black`, `pytest` (100 percent), `ruff`, `pylint`, `prek run --all-files`; check the
  rendered tickets page in a browser against the mockup's list screen.
