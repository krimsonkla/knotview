---
id: kno-01m3q9rx099f-djxzm
ticket: kno-01m3q9rx099f
title: Live reload and integrity issues for documents brainstorm
type: other
created: '2026-09-30T00:08:59.828035Z'
updated: '2026-09-30T00:09:29.103515Z'
---

# kno-01m3q9rx099f — Live reload and integrity issues for documents brainstorm

Story: kno-01m3q9rx099f, "Live reload and integrity issues for documents", story 7 of epic
kno-01m3q9rmck1r. Date: 2026-09-29. Mode: teams-equivalent, quality-engineer challenger, two
rounds.

## Problem

A project whose `:docs-dir` lies outside the tickets directory does not reload when a document
changes, and knot's document issues reach the integrity card as flat lines with absolute paths and
no way to open the document they name.

## Prior art

`KnotCommand.digest` hashes the names and modification times of every markdown file under the
tickets directory, which it asks of knot once and remembers. `integrity()` turns each `check` issue
into a string, `ids code: message (path)`, and the overview card lists them. knot 0.15 reports
`doc_unknown_ticket`, `invalid_doc_type`, `doc_directory_mismatch` and `doc_id_owner_mismatch` with
the document's id and absolute path, and `document show` serves each of those documents.
`legacy_documents_section` names a ticket; `duplicate_doc_id` names an id `document show` refuses as
ambiguous.

## Approach

- **The digest also walks `docs_path`** when it exists and is not inside the tickets directory,
  decided with `Path.is_relative_to`. The default layout keeps its single walk. The docs path is
  remembered like the tickets path, and CLAUDE.md's gotcha says so.
- **`integrity()` returns issue values:** the line as today, the path shown relative to the project
  root when it lies under it (absolute otherwise, the full path as its title), and the ids to link.
  Only the four verified document codes link their ids to `/document/<id>`. Every other code is
  plain, so a code knot adds later degrades rather than links wrongly. An issue may have no id,
  several, or no path.
- **Four call sites move together:** the `Backlog` port, `DeclaredBacklog`, the overview card and
  the real-knot fidelity test.
- **The fake knot's check gains a document mode** copied from knot 0.15's output, its paths
  absolute as knot's are: one under the fake's own root, one outside it, so both branches of the
  path conversion are exercised. No re-recording:
  the recorder's scrub would refuse a document issue's absolute path, and re-recording belongs to
  kno-01m3qdwrjdbx.

## What the challenger changed

- Codes are linked only where verified: `legacy_documents_section` names a ticket and
  `duplicate_doc_id` names an ambiguous id, both of which would 404.
- Containment by `is_relative_to`, since `.tickets-docs` string-prefixes `.tickets`.
- A single walk in the default layout, since the digest runs on a timer.
- Linking ticket ids in other issues is its own ticket.
- The fake's paths are absolute, as knot's always are; relative ones would leave the conversion
  untested. No recording holds an issue with a `path`, which kno-01m3qdwrjdbx now names.
