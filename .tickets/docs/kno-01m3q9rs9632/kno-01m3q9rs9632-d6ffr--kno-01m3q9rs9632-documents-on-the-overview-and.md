---
id: kno-01m3q9rs9632-d6ffr
ticket: kno-01m3q9rs9632
title: Documents on the overview and the tree implementation plan
type: plan
created: '2026-09-30T00:08:58.737348Z'
updated: '2026-09-30T00:09:27.078678Z'
---

# kno-01m3q9rs9632 — Documents on the overview and the tree implementation plan

**Goal:** the overview counts tickets by owned document type, the tree's rows show owned and missing
types, and the footer counts the project's documents.

**Architecture:** `Overview` gains `by_document`, one `Tally` per declared document type over the
tag-narrowed live tickets, each ticket's types read once. `Selection.having(kind)` links to exactly
one type. The docs cell's tag drawing moves into a `_documents.html` macro that
`_ticket_table.html` and `tree.html` both call; `tree.html` sets `show_missing`. `layout.html`'s
footer reads `project.doc_count`. Spec: `kno-01m3q9rs9632-overview-tree-documents-spec.md`.

**Tech stack:** FastAPI, Jinja2, pytest over the TestClient and a declared backlog.

**Test route:** strict — every change is rendered behaviour asserted through the TestClient.

## Coverage

| Spec item | Task |
|-----------|------|
| R1, R2, AC-1, AC-2 | 4 |
| R3, AC-3 | 1, 4 |
| R4, R5, AC-5, AC-6, AC-7 | 3 |
| R6, AC-4 | 4 |
| R7 | 2 |

---

## Files

- Modify: `src/knotview/panel/selection.py`, `src/knotview/panel/overview.py`,
  `templates/overview.html`, `templates/_ticket_table.html`, `templates/tree.html`,
  `templates/layout.html`
- Create: `templates/_documents.html`, `tests/panel/test_overview_tree_documents.py`
- Modify tests: `tests/panel/test_list_documents.py` (the tree test is rewritten to assert dashes)

## Task 1: Selection

- [ ] **Failing unit test:** `Selection(type="task", docs=("plan",), undocumented=True).having("spec")`
  parses to `{"type": ["task"], "doc": ["spec"]}`.
- [ ] `having(kind)`: `replace(self, docs=(kind,), undocumented=False).query_string()`, with a
  docstring saying why it is not `query_string(doc=...)`.

## Task 2: The shared macro

- [ ] Move the docs cell's contents into `{% macro doctypes(ticket, project, show_missing) %}`, every
  value a parameter since an imported macro sees no context, in
  `_documents.html`; `_ticket_table.html` imports and calls it inside `<td class="docs">`.
- [ ] Run `tests/panel/test_list_documents.py` before anything else: output unchanged.

## Task 3: The tree

- [ ] **Failing render tests** (AC-5 to AC-7) over `REQUIRING` from story 3's tests: a node's
  tags in order and linked; a live leaf's dash with its title and none for a closed ticket; an
  orphan's table row dashed. Rewrite story 3's tree test to assert the dash.
- [ ] `tree.html`: `{% set show_missing = true %}` at the top of `block main`, which reaches the
  stray and orphan tables through their includes. `node_row` could read the page's values, but a
  macro that names what it uses is clearer, so it becomes `node_row(node, project)` (both call sites), imports the macro, and
  calls `doctypes(ticket, project, true)` in the node summary and the leaf row after the id.

## Task 4: Overview and footer

- [ ] **Failing tests** (AC-1, AC-2, AC-4): the card's rows and links; with a chosen tag whose
  tickets own nothing, no card; a selection holding `doc=plan` still links spec rows to `doc=spec`;
  the footer with a count of 3 and with 0.
- [ ] `Overview.by_document`: owned sets computed once per live ticket, then
  `Tally(label=kind, count=owned, filter="doc", value=kind)` per `project.doc_types`; empty when
  every count is 0. Say so in the class docstring beside its rule about keeping zeros: zeros stay
  within a drawn card, and the card goes when nothing is owned.
- [ ] `overview.html`: a "by document" card after "by priority", when `overview.by_document`, with
  a muted line "tickets owning each type; a ticket may own several", rows linking through
  `selection.having(tally.value)`.
- [ ] `layout.html`: `· {{ project.doc_count }} documents` after the archived count, always.

## Task 5: Gate

- [ ] `black`, `pytest` (100 percent), `ruff`, `pylint`, `prek run --files <every changed file>` (the commit's own scope) and `prek run --all-files`; check the overview and
  the tree in a browser over a scratch project against the mockup.
