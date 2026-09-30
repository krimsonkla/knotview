---
id: kno-01m3q9rpt69f-dahf4
ticket: kno-01m3q9rpt69f
title: Reading documents implementation plan
type: plan
created: '2026-09-30T00:08:57.909952Z'
updated: '2026-09-30T00:09:25.581948Z'
---

# kno-01m3q9rpt69f — Reading documents implementation plan

**Goal:** the reading layer exposes documents, their order, the types a ticket owns and the
required types it lacks.

**Architecture:** a frozen `Document` value read by `document_from`; document fields on `Ticket`
and `Project`, read tolerantly; four helpers on `Project` that pages use instead of raw fields;
`document list` and `document show` as reads on `KnotCommand` and the `Backlog` protocol, with
`not_found` mapped to `MissingTicket` and `doc_not_found` to a new `MissingDocument` served as a
404. Spec: `kno-01m3q9rpt69f-reading-documents-spec.md`.

**Tech stack:** Python 3.12, FastAPI, pytest over recordings, a fake knot script and a declared
backlog. Gate: `black`, `pytest` at 100 percent, `ruff`, `pylint`, prek, inside `devenv shell --`.

**Commits:** one at `complete-task`.

---

## Files

- Create: `src/knotview/values/document.py`, `src/knotview/values/missing_document.py`
- Modify: `src/knotview/values/ticket.py`, `src/knotview/values/project.py`
- Modify: `src/knotview/reading/knot_envelope.py` (`document_from`, `documents_from`, ticket and
  project fields), `src/knotview/reading/knot_command.py` (`READS`, two reads),
  `src/knotview/reading/backlog.py`
- Modify: `src/knotview/panel/app.py` (a `missing_document` handler)
- Modify: `tests/reading/probe.py` (`PROBE_CONFIG` with `:required-docs`), recordings re-recorded
- Modify: `tests/reading/conftest.py` (fake answers `document list` and `document show`)
- Modify: `tests/panel/declared.py` (documents on the declared tickets and project; the two reads;
  `RefusingBacklog`)
- Tests: `tests/values/test_document.py`, `tests/values/test_project.py`,
  `tests/reading/test_knot_envelope.py`, `tests/reading/test_knot_command.py`,
  `tests/panel/test_routes.py`

## Task 1: Values

- [ ] **Failing tests** in `tests/values/test_project.py` for AC-6 to AC-10 over declared values:
  a project with `doc_types=("spec", "plan", "other")`; documents whose ids, created, titles and
  alphabetical types all disagree (for example ids `x-d1`, `x-d2`, `x-d3`, `x-d4` given in order
  other/"B", spec/"z", plan/"a", memo/"A"); `ordered` gives spec, plan, other, memo; two plans
  titled "b" and "A" come "A" then "b"; `ordered_types(("plan", "memo", "spec"))` gives spec,
  plan, memo; `types_of` over a ticket with documents only and one with `doc_types` only;
  `missing_documents` with `required_docs=(("in_progress", ("spec", "plan")), ("closed", ("plan",)))`
  over tickets owning nothing, a spec, and both; a project with `required_docs=()` gives `()`.
- [ ] **`Document`** in `values/document.py`: `id`, `ticket`, `title`, `type` required;
  `created`, `updated`, `body` as `str | None = None`; docstring states the None/"" contract and
  which command fills what. Frozen, keyword-only.
- [ ] **`Ticket`** gains `documents: tuple[Document, ...] = ()` and `doc_types: tuple[str, ...] =
  ()`, with a comment that pages read them through `Project`.
- [ ] **`Project`** gains `doc_types: tuple[str, ...] = ()`, `required_docs: tuple[tuple[str,
  tuple[str, ...]], ...] = ()`, `doc_count: int = 0` (defaults, so existing declared projects stay
  valid) and the four helpers: `ordered`, `ordered_types`, `types_of`, `missing_documents`. The
  sort key is (declared index or `len(doc_types)`, `title.casefold()`, `id`) — id last so equal
  titles stay stable.
- [ ] **`MissingDocument(UnreadableBacklog)`** in `values/missing_document.py`, mirroring
  `MissingTicket`: `identifier`, code `doc_not_found`, advice to check the ticket's document list.
- [ ] Run `tests/values`, expected pass.

## Task 2: Reading the envelopes

- [ ] **Failing tests** in `tests/reading/test_knot_envelope.py`: AC-1 over `show-parent` and
  `list`; AC-2 over `info` (after Task 4's re-recording, so write it expecting `required_docs ==
  (("in_progress", ("spec", "plan")),)`); `documents_from` over `document-list` gives two with
  created and updated and body None; `document_from` over `document-show` gives the body; a
  document with no id is refused; `project_from` over a hand-made `info` whose `required_docs`
  names `review` (undeclared) and `in_progress` keeps `in_progress` first, then `review` (AC-10).
- [ ] `document_from(stated, *, ticket=None)`: id required (refuse like `ticket_from`); `ticket`
  from the stated `ticket` field, else the argument; title, type via `str(... or "")`; created,
  updated via `_text`; body kept exactly as given when it is a string (so "" stays ""), else
  None — never through `_text`, which would turn an empty body into None. A test reads a stated
  empty body as "".
- [ ] `documents_from(stated, *, attempting)`: a list of documents from `document list`'s
  `documents`, refusing a non-mapping answer.
- [ ] `ticket_from` reads `doc_types` with `_words`, and `documents` with `document_from(one,
  ticket=identifier)` for each mapping entry.
- [ ] `project_from` reads `allowed_values.doc_types`, `counts.doc_count`, and
  `allowed_values.required_docs` into the declared-first pairs.
- [ ] Run, expected pass except AC-2 until Task 4.

## Task 3: The two reads

- [ ] **Failing tests** in `tests/reading/test_knot_command.py` through the fake: `documents` of
  the parent; `document` of `pro-01m2aaaaaaaa-d7spec`; `document` of an unknown id raises
  `MissingDocument`; `documents` of an unknown ticket raises `MissingTicket`; a mode that answers
  another refusal code for `document show` raises plain `UnreadableBacklog`. Extend
  `WRITE_VERBS` with `document add`, `document replace` and `document delete`.
- [ ] Fake knot: `document list` on `pro-01m2aaaaaaaa` says `document-list`, otherwise
  `not-found` with exit 1; `document show` on `pro-01m2aaaaaaaa-d7spec` says `document-show`, on
  `refused` prints an envelope with code `invalid_argument` and exit 1, otherwise
  `document-not-found` with exit 1.
- [ ] `READS` gains `"document list"` and `"document show"`. `KnotCommand.documents(ticket_id)`
  and `document(document_id)`, each catching `UnreadableBacklog` and re-raising by code as the spec
  says; `Backlog` gains both with docstrings.
- [ ] Run, expected pass.

## Task 4: Required documents in the probe

- [ ] In `tests/reading/probe.py` add `PROBE_CONFIG = '{:prefix "pro" :required-docs
  {"in_progress" ["spec" "plan"]}}\n'` and make it `write_probe`'s default; keep `PREFIX_ONLY`
  for a caller that wants none. Re-record with the recorder; expect only `info.json` to change.
- [ ] Assert AC-8 over the recorded project and the declared child and orphan shapes read from
  `show-child` and `list`.
- [ ] Run the reading tests including the slow fidelity test.

## Task 5: Declared backlog and the 404

- [ ] `DeclaredBacklog` gains `documents_value: dict[str, tuple[Document, ...]]` and
  `document_value: dict[str, Document]`; `documents(identifier)` raises `MissingTicket` for an
  unknown ticket; `document(identifier)` raises `MissingDocument` for an unknown one.
  `RefusingBacklog` binds both names to `_refuse`. `PROJECT` gains the probe's doc types and
  requirements; `PARENT` gains the two declared documents.
- [ ] `app.py` registers `MissingDocument` with a `missing_document` handler rendering
  `unknown.html` at 404 with `looking_for=f"document called {refusal.identifier}"`.
- [ ] Test in `tests/panel/test_routes.py` (AC-5): a throwaway route on the assembled app that
  calls `backlog.document("nope")` answers 404 with the ticket list offered. No real route reads a
  document yet; story 6 adds one.
- [ ] Run the panel tests.

## Task 6: Gate

- [ ] `black`, `pytest` (100 percent), `ruff`, `pylint`, `prek run --all-files`.
