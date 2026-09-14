---
id: kno-01m2g51dwp4n
title: Sticky tag filtering across every view
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-14T14:27:19.573928Z'
updated: '2026-09-14T14:30:55.209947Z'
closed: '2026-09-14T14:30:55.209947Z'
assignee: Jason Risch
---

## Description
knot tickets carry tags, and the panel only uses them as a single `tag=` filter on the tickets page. A reader who cares about one slice of the backlog (a tag like `p0` or `auth`) has to re-apply it on every page. The tags should apply to whatever view the reader is on: overview counts, queues, tree, tickets, and the attention and recently-changed cards all narrow to the selected tags, and a tag selected on one view stays in effect on every view until cleared.

## Design
The selection lives in a cookie in the reader's browser, never on the server and never in a ticket: the panel stays read-only over the backlog. Every page's bar shows the active tags as chips, each removable, an input to add one (with the tags seen on live tickets offered as suggestions), and a clear link. A `/tags` route, a GET like every other, sets or drops a tag in the cookie and redirects back to the page the reader was on; the redirect target must be a path on this panel. A ticket matches when it carries every selected tag. The ticket page itself is not narrowed, since it shows one ticket by id, but its bar shows the tags like every other page.

## Notes

**2026-09-14T14:30:54.396681Z**

Task completed: the reader's chosen tags live in a cookie (knotview_tags) in their browser; the /tags route, a GET, adds, drops or clears a tag and redirects back to a path on this panel only; every view (overview counts, queues, attention cards, tickets, tree) narrows to tickets carrying all chosen tags until cleared; the bar on every page shows the chosen tags as removable chips, an input with the live tickets' tags as suggestions, and a clear link. The ticket page shows one ticket by id and is not narrowed. The panel writes nothing to the backlog.
