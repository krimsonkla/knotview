---
id: kno-01m3q9rvrdst-d5h7t
ticket: kno-01m3q9rvrdst
title: A page to read a document implementation plan
type: plan
created: '2026-09-30T00:08:59.549858Z'
updated: '2026-09-30T00:09:28.591616Z'
---

# kno-01m3q9rvrdst — A page to read a document implementation plan

**Goal:** a reader opens `/document/<id>`, reads the document, moves between its ticket's documents
and gets back to the ticket.

**Architecture:** `Pages.document` reads `document(id)`, then `documents(doc.ticket)` and
`ticket(doc.ticket)`, each catching `MissingTicket` locally; documents are ordered through
`Project.ordered`. `prose.outlined(text)` renders the body demoted one level and returns the HTML
with the outline from the same traversal, heading ids set through markdown-it's `attrSet`.
The page method passes the HTML and the outline to `document.html`, which marks only that HTML
safe, as the ticket page does with its `prose` output. `static/document.js` scrolls the current tab into view. Spec:
`kno-01m3q9rvrdst-document-page-spec.md`.

**Tech stack:** FastAPI, Jinja2, markdown-it-py, pytest over the TestClient and a declared backlog.
**Test route:** strict.

## Coverage

| Spec item | Task |
|-----------|------|
| R3, R4, R5 (renderer), AC-2, AC-4 | 1 |
| R1, R2, R5 (panel), R8, R9, AC-1, AC-3, AC-5, AC-6 | 2 |
| R6, R7, AC-7 to AC-10 | 3 |

## Files

- Modify: `src/knotview/panel/prose.py`, `src/knotview/panel/app.py`, `static/panel.css`,
  `tests/panel/declared.py` (prefix resolution, as knot does)
- Create: `templates/document.html`, `static/document.js`, `tests/panel/test_prose_outline.py`,
  `tests/panel/test_document_page.py`

## Task 1: The renderer

- [ ] **Failing unit tests** in `test_prose_outline.py`:
  - `outlined("# Plan\n\n## Plan\n\n### Deep\n")` gives headings `h2 id="doc-plan"`,
    `h3 id="doc-plan-2"`, `h4 id="doc-deep"`, and an outline of the first two only, as
    `(2, "Plan", "doc-plan")` and `(3, "Plan", "doc-plan-2")`;
  - a heading `## **Rollout** now` has outline text "Rollout now";
  - a heading containing `"><script>x</script>` renders escaped, in its text and in its id;
  - raw HTML in the body is escaped;
  - a heading of only punctuation gets `doc-section`.
- [ ] `outlined(text) -> tuple[str, tuple[Outline, ...]]`:
  - parse with the existing `_RENDERER`;
  - demote by one level;
  - per `heading_open`, build the slug from the next inline token's children, joining `text` and
    `code_inline` content, lowercased, with runs of non-alphanumerics becoming `-` and trimmed,
    falling back to `section`;
  - dedupe with `-2`, `-3` and prefix `doc-`;
  - set the id with `token.attrSet("id", anchor)`;
  - keep the outline entry when the demoted level is 2 or 3.

  `Outline` is a frozen dataclass `(level, text, anchor)`, the text plain. Both `rendered` and
  `outlined` go through one private `_walk(text, demote)` that parses and demotes, returning the
  tokens; `rendered` keeps demoting by two and its output is unchanged (the existing prose tests
  hold that).

## Task 2: The page

- [ ] `DeclaredBacklog.document` resolves an exact id first, then a prefix naming the owning ticket in
  full plus `-d` and matching exactly one of that ticket's documents, as knot does; several or none raise `MissingDocument`. A unit test in
  `test_document_page.py` covers each of the three.
- [ ] `KnotCommand.document` maps `ambiguous_doc` to `MissingDocument` as it does `doc_not_found`,
  tested through the fake knot in `tests/reading/test_knot_command.py` the way `doc_not_found`
  is. (Modify: `src/knotview/reading/knot_command.py`.)
- [ ] **Failing render tests** in `test_document_page.py`, over `PARENT_DOCUMENTS` with bodies:
  - AC-1: the breadcrumb links `/ticket/pro-01m2aaaaaaaa` with "The parent"; there is one `<h1>`
    holding the title; the type tag, the id and the updated stamp appear; the body's headings
    render as h2; one outline link's href equals one heading's id;
  - AC-3: an unknown id gives 404 and "document called";
  - AC-4: an empty body gives "This document is empty.";
  - AC-5: a document whose ticket is not declared gives 200, the body and the bare ticket id, and
    no "ticket called";
  - AC-6: a document owned by the closed ticket gives 200.
- [ ] `Pages.document(request, identifier)`:
  - read the document;
  - read `documents` and `ticket` for `doc.ticket`, each through a helper that returns `()` or
    `None` on `MissingTicket`;
  - order the documents with `(doc,)` as the fallback;
  - render `document.html` with `document`, `owner`, `documents`, `body` and `outline` (from
    `outlined(doc.body)` when the body is non-empty), and `selection=Selection()`.
- [ ] Add `("/document/{identifier}", "document", HTMLResponse)` to `ROUTES`, and add
  `/document/{identifier}` to the route list in `tests/panel/test_routes.py` and
  `/document/pro-01m2aaaaaaaa-d2plan` to its rendered-paths parameter.
- [ ] `document.html`:
  - a header with the crumb, h1, `.doctype`, id and `stamp(updated)`;
  - a `.docpage` grid with `<article class="card prose">{{ body | safe }}</article>`, the one
    `safe` on the page, over the renderer's output alone;
  - an aside `dl` with the ticket, type, created and updated, and "on this page" when the outline
    is non-empty.

  An empty body is stated instead of an empty article.

## Task 3: Tabs, menu and position

- [ ] **Failing render tests:**
  - AC-7: the tabs read spec before plan; the plan's tab carries `aria-current="page"`; "2 of 2";
  - AC-8: `<details class="all">` lists "spec" and "plan" group labels with their links and dates;
  - AC-9: reached by `pro-01m2aaaaaaaa-d2`, the plan's tab is current and every tab href is a full
    id;
  - AC-10: a single-document ticket has no `class="tabs"`, no `class="all"` and no " of ".
- [ ] `document.html`: when `documents | length > 1`, add:
  - a `.tabstrip` with `nav.tabs` of links, `aria-current="page"` where `one.id == document.id`;
  - `details.all` over `groups`, runs of one type in the given order built by `_grouped` in `app.py` (Jinja's `groupby` sorts by name);
  - `position` (computed by the page method) "of" the count in the header.
- [ ] `panel.css`: `.doctype`-sized tabs on one line, `overflow-x: auto`, the faded edge by
  `mask-image`, and the `details.all` menu absolutely placed, all from the mockup and using the
  existing tokens.
- [ ] `static/document.js`: on load, `document.querySelector('.tabs [aria-current]')`
  `?.scrollIntoView({block: 'nearest', inline: 'nearest'})`. Included by `document.html` with the
  asset stamp.

## Task 4: Gate

- [ ] `black`, `pytest` (100 percent), `ruff`, `pylint`, `prek run --files <changed>` and `prek run --all-files`. Check the
  page in a browser over a scratch project with nine documents on one ticket, against the mockup's
  document screen, at desktop and phone widths.
