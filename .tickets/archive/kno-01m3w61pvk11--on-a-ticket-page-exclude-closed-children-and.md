---
id: kno-01m3w61pvk11
title: On a ticket page, exclude closed children and order children by status
status: closed
type: task
priority: 2
mode: afk
created: '2026-10-01T16:51:32.338744Z'
updated: '2026-10-01T17:01:34.342502Z'
closed: '2026-10-01T17:01:34.342502Z'
assignee: Jason Risch
---

On an epic's page, or any ticket with children, the children card lists every child in knot's order, closed ones mixed in with the rest. On a long-running epic most children are closed, and the work still to do is buried among them.

## Design

- Children are ordered by status, in the order the project declares its statuses (open, in_progress, closed here), with knot's order kept within a status.
- The reader can exclude the closed children, those in a terminal status, from the card. The choice is part of the page's URL, so it is a link a reader can keep, and the card says how many closed children are hidden.

## Notes

**2026-10-01T16:51:40.688020Z**

Starting work on this task.

**2026-10-01T17:01:32.729728Z**

Done in 93c6763 and c707ea9.

On a ticket page, children are listed by the project's declared status order: open, in_progress, then closed here. Undeclared statuses come after those, missing references last, and knot's order is kept within each status. The siblings card ("also under") uses the same order, and counts the rows it draws.

The children card's heading carries a link to hide the closed children:
- Shown, it reads "children 7" with "hide closed (4)".
- Hidden, through `?children=live`, it reads "children 3 of 7" with "show closed".

The card stays while it hides anything, so an epic whose children are all closed still offers the way back. The toggle appears only when a closed child exists. Any other value of the parameter shows everything, and no link on the page carries the choice except the toggle. Blocked by, blocking and linked keep knot's order.

Checked in the browser on this repository's documents epic: "children 7, hide closed (7)", then "children 0 of 7, show closed".

Reviewed:
- brainstorm by the quality engineer (two rounds);
- spec and plan by their reviewers (both clean) and the solution architect;
- /code-review high: one finding fixed (a kept hide link drew "3 of 3" once nothing was closed), then no findings.

The tree's children keep knot's order for now; ordering them is filed as kno-01m3w6eyzcjx. The brainstorm, spec and plan are attached as documents.
