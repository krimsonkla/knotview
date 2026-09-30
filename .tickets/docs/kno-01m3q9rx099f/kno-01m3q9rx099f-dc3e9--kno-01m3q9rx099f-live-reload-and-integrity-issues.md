---
id: kno-01m3q9rx099f-dc3e9
ticket: kno-01m3q9rx099f
title: Live reload and integrity issues for documents implementation plan
type: plan
created: '2026-09-30T00:08:59.982383Z'
updated: '2026-09-30T00:09:29.350455Z'
---

# kno-01m3q9rx099f — Live reload and integrity issues for documents implementation plan

**Goal:** every document change reloads an open page, and each document issue on the integrity card
shows a readable path and links the document it names.

**Architecture:** `Project` gains `docs_path` and `project_root` from `info`'s paths. `KnotCommand`
remembers the paths it needs from one `info`, as it does the tickets directory today. The digest
adds the docs tree when it lies outside the tickets tree. `integrity()` returns `Issue` values
(`values/issue.py`) built in the reading layer. The port, the snapshot, the overview value, the
declared double, the card and the real-knot test move to `Issue` together. Spec:
`kno-01m3q9rx099f-docs-live-integrity-spec.md`.

**Tech stack:** Python, FastAPI, Jinja2, pytest with the fake knot and a declared backlog.
**Test route:** strict.

## Coverage

| Spec item | Task |
|-----------|------|
| R1, R2, R3, AC-1 to AC-4 | 1 |
| R4, R5, AC-5 to AC-8 (values) | 2 |
| R6, AC-5 to AC-8 (card) | 3 |

## Files

- Create: `src/knotview/values/issue.py`, `tests/reading/test_digest_documents.py`,
  `tests/reading/test_issues.py`
- Modify: `values/project.py`, `reading/knot_envelope.py`, `reading/knot_command.py`,
  `reading/backlog.py`, `reading/snapshot.py`, `panel/overview.py`, `templates/overview.html`,
  `tests/panel/declared.py`, `tests/reading/conftest.py`, `tests/reading/test_knot_command.py`,
  `tests/reading/test_real_knot.py`, `tests/reading/test_snapshot.py`,
  `tests/panel/test_overview.py`, `CLAUDE.md` (gotcha)

## Task 1: The digest

- [ ] **Failing tests** in `test_digest_documents.py`. The fake's `info` gains an env-controlled
  `docs_path`, defaulting to `<tickets>/docs`. Tests:
  - AC-1: a docs dir beside `.tickets` (`<root>/docs`); writing a file there moves the digest;
  - AC-2: with the default layout, the digest equals a hash over each file once (compare against a
    `KnotCommand` whose docs path is unset);
  - AC-3: `<root>/.tickets-docs` is walked;
  - AC-4: a missing docs dir leaves the digest as the tickets tree's.
- [ ] `Project`: `docs_path: str = ""`, `project_root: str = ""`; `project_from` reads both from
  `paths`.
- [ ] `KnotCommand`: replace `_tickets()` with `_where()`, which remembers `(tickets, docs, root)`
  from one `project()`. `digest` stamps the tickets tree, then the docs tree when
  `docs.is_dir() and not docs.is_relative_to(tickets)`, with names relative to the tree's own root
  and prefixed so the two sets cannot collide.
- [ ] CLAUDE.md gotcha: "The digest asks knot for the tickets and documents directories once per
  `KnotCommand`...".

## Task 2: Issue values

- [ ] `values/issue.py`:
  `Issue(text: str, path: str = "", shown: str = "", document_ids: tuple[str, ...] = ())`, frozen,
  kw_only, with a docstring on why only verified codes link, and
  `Issue.found(text, path, root, document_ids=())`, the one place `shown` is derived (relative when
  `Path(path).is_relative_to(root)`, else the path; empty with no path). `_issue` and every test
  build through it.
- [ ] **Failing tests** in `test_issues.py` through `_issue(stated, root)`:
  - `invalid_doc_type` under the root: text without the path, `shown` relative, `document_ids` the
    id;
  - the same outside the root: `shown` absolute;
  - `legacy_documents_section`, `duplicate_doc_id` and an unknown code: no document ids;
  - no ids and no path: text only;
  - several ids on a linkable code: all linked.
- [ ] The fake's `check` gains a `documents` mode printing three issues copied from knot 0.15:
  - `invalid_doc_type`, path `<root>/.tickets/docs/pro-01m2aaaaaaaa/pro-01m2aaaaaaaa-d5memo--memo.md`;
  - `doc_unknown_ticket`, path `/elsewhere/docs/pro-01m2zzzzzzzz/pro-01m2zzzzzzzz-d1x--orphan.md`;
  - `legacy_documents_section`, ids `["pro-01m2aaaaaaaa"]`.

  A test through `fake(check="documents").integrity()` asserts the three values.
- [ ] `knot_command.py`:
  - `LINKED = frozenset({"doc_unknown_ticket", "invalid_doc_type", "doc_directory_mismatch", "doc_id_owner_mismatch"})`;
  - `_described` keeps its line but no longer appends the path, since the card shows it;
  - `_issue(stated, root)` builds `Issue` (a non-dict issue gives `Issue(text=str(stated))`);
  - `integrity()` returns `tuple[Issue, ...]` using the remembered root.
- [ ] Port and callers: `Backlog.integrity -> tuple[Issue, ...]`, `Snapshot.integrity`,
  `Overview.integrity`, `DeclaredBacklog.integrity_value`. `test_knot_command.py`,
  `test_snapshot.py` and `test_real_knot.py` read `.text`. `test_real_knot.py` also asserts the
  recorded unknown_id issue has no document ids.

## Task 3: The card

- [ ] **Failing render tests** in `test_overview.py`:
  - AC-5: an `Issue` with `document_ids=("pro-01m2aaaaaaaa-d5memo",)`, `shown` relative and `path`
    absolute renders `<a href="/document/pro-01m2aaaaaaaa-d5memo">`, the shown path, and
    `title="<absolute>"`;
  - AC-6: an issue without documents renders no `/document/`;
  - AC-7: text only renders no path element;
  - AC-8: an absolute shown path renders as given.

  The existing listing test moves to issue values built by `_issue` from the recorded
  check-issues.
- [ ] `overview.html`: each `<li>` holds the text; then each document id as
  `<a href="/document/{{ id | segment }}">{{ id }}</a>`; then, when shown,
  `<span class="id" title="{{ issue.path }}">{{ issue.shown }}</span>`.

## Task 4: Gate

- [ ] `black`, `pytest` (100 percent), `ruff`, `pylint`, and `prek run --files <changed>` and
  `--all-files`.
- [ ] Browser check over a scratch project with the three document issues and a docs dir outside
  `.tickets`. Editing a document there reloads the open overview.
