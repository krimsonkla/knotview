---
id: kno-01m3qtd4ax4g
title: Lists and the ticket page disagree about a misfiled document
status: open
type: task
priority: 2
mode: afk
created: '2026-09-30T00:11:05.948728Z'
updated: '2026-09-30T04:57:01.141871Z'
assignee: ''
---

knot 0.15 derives a listing row's doc_types from the documents directory layout, but `show` and `document list` derive a ticket's documents from each file's `ticket:` frontmatter. When a document is filed under one ticket's directory but names another (knot check: doc_directory_mismatch), the two disagree. The panel then shows the named ticket owning a spec in the lists, with a link to a documents card that its own page does not draw, while that page dashes the spec as missing. Found in the adversarial review of kno-01m3q9rtgqa9. Only reachable with an integrity issue, which the overview's integrity card already reports and links.

## Design

Decide whether the lists should agree with the ticket page, for example by reading doc_types from `document list` for rows whose ticket appears in a doc_directory_mismatch issue, or whether to report the divergence to knot upstream so its listing reads the same source as `show`. Reading `document list` for every row is not acceptable, since the lists render on every live reload.

## Notes

**2026-09-30T04:57:01.141871Z**

Reproduced against knot 0.15.0. This corrects the description above: the listing does not read the directory layout.

The setup: a document filed under `docs/pro-01m2aaaaaaaa/` whose `ticket:` field names `pro-01m2dddddddd`.
- `knot list`: the row for pro-01m2dddddddd, the ticket the frontmatter names, carries `doc_types: ["spec"]`. The parent's row carries none.
- `knot show` and `knot document list`: neither ticket owns the document.
- `knot check`: reports `doc_directory_mismatch` for the document id, which the overview's integrity card shows and links.

So knot disagrees with itself: its listing credits the ticket the frontmatter names, while `show` and `document list` credit nobody. The panel shows each answer where it reads it.

Options considered:
- Correct it in the panel: run `knot check` on every list render, then read each misfiled document to drop its type from the wrongly credited ticket.
- Report it to knot upstream, and drop the question once knot's listing and `show` read the same source.

On hold by the developer's decision; left open.
