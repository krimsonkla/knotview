---
id: kno-01m3q9rnkpy7-dr3qt
ticket: kno-01m3q9rnkpy7
title: knot 0.15 baseline implementation plan
type: plan
created: '2026-09-30T00:08:57.625856Z'
updated: '2026-09-30T00:09:24.856372Z'
---

# kno-01m3q9rnkpy7 — knot 0.15 baseline implementation plan

**Goal:** every recording, the CI fidelity job and every version reference describe knot 0.15.0,
with documents in the probe.

**Architecture:** one probe module shared by the recorder and the fidelity fixture writes
tickets, documents and a given `.knot.edn`. The recorder runs record, normalize, guard, write,
and writes nothing when the guard or the clean-check assertion refuses. CI installs the tagged
knot and only verifies. Spec: `kno-01m3q9rnkpy7-knot-015-baseline-spec.md`.

**Tech stack:** Python 3.12, pytest, knot 0.15.0 from the devenv shell. Gate: `black`, `pytest`
at 100 percent line and branch over `knotview`, `ruff`, `pylint`, the prek hooks, all inside
`devenv shell --`.

**Commits:** one commit at `complete-task` on `jr/kno-01m3q9rmck1r-attached-documents`,
carrying `devenv.yaml` and `devenv.lock` but never `devenv.config.toml`.

---

## Changes since last cycle

- Documents are literal file text in `DOCUMENTS`, like `TICKETS`, with no `_document` helper, so
  pylint's argument and builtin-name rules have nothing to object to.
- Task 2 names the import swap in `record_envelopes.py` as its own step, so the recorder, and
  the fast test that imports it, stop importing the pytest module and `knotview`.
- Normalizing rewrites each probe's own root, as today; the scratch directory is only in the
  guard's forbidden set.
- The refusal path is a pure `finish(recordings, forbidden, write)`, tested with a fake writer,
  so AC-4's "writes no file" is asserted without knot.
- `git_user_name()` runs git with `check=False`, strips the output, and returns "" on any
  failure.

## Files

- Create: `tests/reading/probe.py` (TICKETS, DOCUMENTS, PREFIX_ONLY, `write_probe`)
- Modify: `tests/reading/test_real_knot.py` (import from the probe; fixture uses `write_probe`)
- Modify: `tests/reading/record_envelopes.py` (stages; `leaks`, `vetted`; clean probe filtered)
- Modify: `tests/reading/envelopes/__init__.py` (three recordings; docstring version)
- Create: `tests/reading/test_record_envelopes.py` (fast tests of `leaks` and `vetted`)
- Create: `tests/reading/test_recorded_documents.py` (fast assertions over the recordings)
- Re-record: `tests/reading/envelopes/*.json`, plus `document-list.json`, `document-show.json`,
  `document-not-found.json`
- Modify: `tests/reading/test_knot_envelope.py:84`, `tests/panel/declared.py:17`, `CLAUDE.md:24`
- Modify: `.github/workflows/ci.yml` (tag v0.15.0; drop `KNOT_VERSION`; a verify-only comment)
- Commit as is: `devenv.yaml`, `devenv.lock`

## Task 1: The probe module

- [ ] **Step 1:** create `tests/reading/probe.py`. Move `TICKETS` from `test_real_knot.py`
  unchanged. Add `PREFIX_ONLY = '{:prefix "pro"}\n'` and `DOCUMENTS`, four literal files in the
  same style as `TICKETS`, keyed by path under `.tickets/`:

  | path under `.tickets/docs/` | id | title | type | created |
  |---|---|---|---|---|
  | `pro-01m2aaaaaaaa/pro-01m2aaaaaaaa-d2plan--rollout-plan.md` | `pro-01m2aaaaaaaa-d2plan` | Rollout plan | plan | 2026-09-06T10:00:00.000000Z |
  | `pro-01m2aaaaaaaa/pro-01m2aaaaaaaa-d7spec--design-spec.md` | `pro-01m2aaaaaaaa-d7spec` | Design spec | spec | 2026-09-02T10:00:00.000000Z |
  | `pro-01m2bbbbbbbb/pro-01m2bbbbbbbb-d4spec--child-spec.md` | `pro-01m2bbbbbbbb-d4spec` | Child spec | spec | 2026-09-04T10:00:00.000000Z |
  | `pro-01m2cccccccc/pro-01m2cccccccc-d9note--closing-notes.md` | `pro-01m2cccccccc-d9note` | Closing notes | other | 2026-08-02T10:00:00.000000Z |

  Each file's frontmatter is id, ticket, title, type, created and updated (equal to created),
  quoted as the tickets' instants are; the spec's body holds a heading, an emphasis, a link and
  a table. A comment above `DOCUMENTS` says why the plan's id sorts before the spec's.

  `write_probe(root, tickets, documents, knot_edn=PREFIX_ONLY)` runs `knot init`, writes
  `.knot.edn`, writes each ticket under `.tickets/`, and writes each document only when the owner
  directory's name appears in some written ticket's filename. Imports: `subprocess`, `pathlib`.

- [ ] **Step 2:** `test_real_knot.py` imports `TICKETS, DOCUMENTS, write_probe` from
  `tests.reading.probe`; the fixture becomes `write_probe(root, TICKETS, DOCUMENTS)`.

## Task 2: The recorder's stages and its guard

- [ ] **Step 0:** replace `from tests.reading.test_real_knot import TICKETS` in
  `record_envelopes.py` with `from tests.reading.probe import DOCUMENTS, TICKETS, write_probe`.
- [ ] **Step 1: failing fast tests**, `tests/reading/test_record_envelopes.py`:

```python
from tests.reading.record_envelopes import finish, leaks, vetted


def test_a_leak_is_named_by_recording_and_string():
    found = leaks({"info": '{"p": "/tmp/xyz/probe/.tickets"}', "list": "[]"}, {"/tmp/xyz", "alice"})
    assert found == [("info", "/tmp/xyz")]


def test_an_empty_or_missing_forbidden_string_is_not_searched_for():
    assert leaks({"info": "anything"}, {"", None}) == []


def test_a_dirty_clean_check_refuses_and_a_clean_set_passes():
    clean = '{"ok": true, "data": {"issues": []}}'
    dirty = '{"ok": false, "data": {"issues": [{"code": "doc_unknown_ticket"}]}}'
    assert vetted({"check-clean": clean}, {"/tmp/x"}) == []
    assert vetted({"check-clean": dirty}, {"/tmp/x"}) == ["check-clean reports 1 issue"]
    assert vetted({"check-clean": clean, "info": "/tmp/x/a"}, {"/tmp/x"}) == [
        "info contains /tmp/x"
    ]


def test_a_refused_set_writes_nothing_and_a_clean_one_writes_everything():
    written = []
    clean = '{"ok": true, "data": {"issues": []}}'
    assert finish({"check-clean": clean, "info": "/tmp/x"}, {"/tmp/x"}, written.append) == 1
    assert not written
    assert finish({"check-clean": clean, "info": "ok"}, {"/tmp/x"}, written.append) == 0
    assert sorted(written) == ["check-clean", "info"]
```

- [ ] **Step 2: run**, expected import failure.
- [ ] **Step 3:** in `record_envelopes.py`, add `leaks(recordings, forbidden) -> list[tuple[str,
  str]]` (drops falsy needles; order by recording name, then needle) and `vetted(recordings,
  forbidden) -> list[str]` (leaks as `"<name> contains <needle>"`, plus
  `"check-clean reports <n> issue(s)"` when its `data.issues` is non-empty). Restructure
  `main()`: build both probes inside one scratch directory with `write_probe`, the clean one from
  the parent and the archived child with `DOCUMENTS`; record every entry into a dict, applying
  `scrubbed()` with each probe's own root as today (the normalize stage); compute
  `forbidden = {str(scratch), str(Path(scratch).resolve()), str(Path.home()), git_user_name()}`;
  return `finish(recordings, forbidden, write)`. `finish` prints each of `vetted()`'s problems to
  stderr and returns 1 without calling `write`, or calls `write(name)` for every recording and
  returns 0. `git_user_name()` runs `git config user.name` with `check=False`, strips it, and
  returns "" on any failure.
- [ ] **Step 4: run**, expected pass. The recorder's `main` stays untested by the fast suite,
  as today; it is exercised by running it in Task 3.

## Task 3: The recordings

- [ ] **Step 1:** add to `RECORDINGS`:

```python
    ("document-list", "document list", ("pro-01m2aaaaaaaa",)),
    ("document-show", "document show", ("pro-01m2aaaaaaaa-d7spec",)),
    ("document-not-found", "document show", ("pro-01m2aaaaaaaa-dnope",)),
```

  and change the docstring's version to 0.15.0 and its probe description to mention the four
  documents.
- [ ] **Step 2: failing fast test**, `tests/reading/test_recorded_documents.py`, asserting
  AC-1 and AC-2 over `envelope(...)`: two entries in `show-parent`'s `data.documents`; a row with
  `doc_types` in each of list, ready, blocked, closed; a row without in list and ready; the five
  `info` fields; `scanned.docs` in both checks; `document-list` has two documents with created
  and updated; `document-show` has a `body`; `document-not-found` is `ok` false with
  `doc_not_found`.
- [ ] **Step 3: record:** `devenv shell -- uv run python -m tests.reading.record_envelopes`.
  Expected: every file printed and exit 0. If it refuses, fix the cause; never hand-edit.
- [ ] **Step 4: run** the new test and the slow fidelity test:
  `devenv shell -- pytest --no-cov tests/reading -q`. Expected: all pass.

## Task 4: Version references

- [ ] `tests/reading/test_knot_envelope.py:84` asserts `("pro", "0.15.0")`.
- [ ] `tests/panel/declared.py:17` `knot_version="0.15.0"`.
- [ ] `CLAUDE.md:24` says JSON recorded from knot 0.15.0.
- [ ] Search: `git grep -n "0\.12\.0" -- ':!.tickets' ':!docs/ai-assistant-ideation'` prints
  nothing.

## Task 5: CI

- [ ] In `.github/workflows/ci.yml` the fidelity job installs `--git/tag v0.15.0`; the unread
  `KNOT_VERSION` env is removed; a comment above the job says it verifies the recordings against
  the tagged knot and never records them.

## Task 6: Gate, commit, CI

- [ ] Full gate: `black`, `pytest` (100 percent), `ruff`, `pylint`, `prek run --all-files`.
- [ ] `complete-task` commits the work with `devenv.yaml` and `devenv.lock`, never
  `devenv.config.toml`.
- [ ] Push the branch and read the CI fidelity job's log for knot 0.15.0 and a pass (AC-6).
