---
id: kno-01m3q9rx099f-dr4g9
ticket: kno-01m3q9rx099f
title: Live reload and integrity issues for documents design spec
type: spec
created: '2026-09-30T00:09:00.114129Z'
updated: '2026-09-30T00:09:29.604647Z'
---

# Live reload and integrity issues for documents Design Spec

**Story:** Live reload and integrity issues for documents (kno-01m3q9rx099f)
**Tier:** Feature — the digest, the integrity read's shape, and the card
**Brainstorm:** `docs/ai-assistant-ideation/kno-01m3q9rx099f-docs-live-integrity-brainstorm.md`

## Changes since last cycle

- `Issue` lives in `values/`, keyword-only and frozen, with one constructor deriving the shown
  path from the full path and the project root, so the reader and the test double cannot disagree;
  its ids field is `document_ids`, not `documents`, which elsewhere holds document values.
- The tickets, documents and root paths come from one `info` read, remembered together.
- The issue's text drops the `(path)` suffix `_described` used to append, since the value carries
  the path and the card shows it once (R4).

## Problem

A project that keeps documents outside the tickets directory does not reload when one changes. The
integrity card lists knot's document issues as flat lines with absolute paths and no link to the
document.

## Goal

Every document change reloads an open page, and each document issue on the integrity card shows a
readable path and links the document it names.

## Scope

**In scope:** walking the docs directory in the digest; issue values from `integrity()`; the card's
links and paths; the fake knot's document issues.
**Out of scope:** linking ticket ids in other issues (its own ticket); re-recording envelopes with a
document issue (kno-01m3qdwrjdbx).
**Non-goals:** fixing issues; reading document contents for the digest.

## Requirements

| ID | Priority | Requirement |
|----|----------|-------------|
| R1 | MUST | `Project` carries knot's `docs_path`. |
| R2 | MUST | The digest also covers the markdown files under the docs path when that directory exists and is not inside the tickets directory, decided by path containment rather than string prefix; in the default layout it walks one tree once. |
| R3 | MUST | The tickets and docs paths and the project root come from one `info` read per reader, kept together; CLAUDE.md's gotcha covers both directories. |
| R4 | MUST | `integrity()` returns issue values carrying the line as today less its trailing `(path)`, which the value carries separately so the card shows it once, the path (relative to the project root when under it, else absolute, with the full path kept), and the ids to link. An issue with no ids, several ids or no path is carried as it is. |
| R5 | MUST | Only issues coded `doc_unknown_ticket`, `invalid_doc_type`, `doc_directory_mismatch` or `doc_id_owner_mismatch` link their ids, each to `/document/<id>`; every other code renders as plain text. |
| R6 | MUST | The integrity card renders each issue's text, its links and its path with the full path as a title. |

## Design

**Approach:** `project_from` reads `docs_path`. `KnotCommand` remembers the docs path beside the
tickets path; the digest adds that tree's files when it is outside. `integrity()` builds an `Issue`
per check entry, keeping `_described`'s text; the Backlog port, `DeclaredBacklog`, the overview card
and the real-knot fidelity test change together.

**Interfaces and contracts:** `Issue(text, path, shown, document_ids)`: `path` the full path or empty,
`shown` its display form, `document_ids` the ids to link (empty unless the code is one of the four). A
link to a document deleted since the check lands on the document page's 404.

**Prior art to mirror:** `digest` and `_tickets` for the remembered path; `_described` for the text;
the overview's integrity card.

**Key decisions:** the four codes are verified against knot 0.15; `duplicate_doc_id` names an id knot
refuses as ambiguous and `legacy_documents_section` names a ticket, so both stay plain. The fake
knot's document issues are copied from knot 0.15's output rather than recorded, since recording
needs the recorder's scrub to cover check paths.

## Acceptance Criteria

### Story 1: When a document changes, I want the open page to follow it.

**AC-1** — Given a docs path outside the tickets directory, when a document there is written, then
the digest changes.
**AC-2** — Given the default layout, when the digest is computed, then each document file is counted
once.
**AC-3** — Given a docs path whose name string-prefixes the tickets directory's but is not inside it
(`.tickets-docs`), when a document there changes, then the digest changes.
**AC-4** — Given a docs path that does not exist, when the digest is computed, then it is the
tickets directory's digest alone.

### Story 2: When knot reports a document issue, I want to see where and open it.

**AC-5** — Given a check with an `invalid_doc_type` issue whose path lies under the project root,
when the overview renders, then the card shows the message, the path relative to the root with the
full path as its title, and a link to `/document/<id>`.
**AC-6** — Given issues coded `legacy_documents_section` (a ticket id), `duplicate_doc_id` and an
unknown code, when the overview renders, then none of them links to `/document/`.
**AC-7** — Given an issue with no ids and no path, when the overview renders, then its text shows
alone.
**AC-8** — Given a path outside the project root, when the card renders, then it shows the absolute
path.

### Traceability
| Story AC | Spec ACs | Notes |
|----------|----------|-------|
| A change to a document under a custom :docs-dir outside the tickets directory moves the digest | AC-1, AC-2, AC-3, AC-4 | |
| Document issues from knot check render on the integrity card with their path | AC-5 to AC-8 | links the document for the four verified codes |

## Boundaries
- ✅ Always: take issue text from `_described`, which stops appending the path; keep the digest to
  names and times.
- 🚫 Never: infer a linkable code from its name; read document contents in the digest.

## Testing Strategy
AC-1 to AC-4 are reading tests through the fake knot over temporary directories; AC-5 to AC-8 are
unit tests of the issue values through the fake's document mode and rendered overview tests over a
declared backlog. The fake's document issues carry absolute paths, as knot's do: one under its own
root and one outside it, so both display forms come from a real conversion. No committed recording
holds an issue with a `path`; kno-01m3qdwrjdbx is to record one.

---
After implementing, compare results against each acceptance criterion above
and list any unmet requirements.
