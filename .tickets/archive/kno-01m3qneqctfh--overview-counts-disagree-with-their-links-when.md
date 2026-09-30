---
id: kno-01m3qneqctfh
title: Overview counts disagree with their links when the URL carries closed=1
status: closed
type: task
priority: 2
mode: afk
created: '2026-09-29T22:44:35.353703Z'
updated: '2026-09-30T04:04:25.274190Z'
closed: '2026-09-30T04:04:25.274190Z'
assignee: Jason Risch
---

The overview's "by" cards count live tickets, but each row's link carries the reader's selection, including `closed=1`. On `/?closed=1`, a row can say "chore 0" while its link lists a closed chore. The same happens on the "by document" card ("other 0" returns the closed ticket that owns an other). Found during the adversarial review of kno-01m3q9rs9632. It predates that story and affects every card.

## Design

Decide one rule for the whole overview. Either the counts follow `closed=1` (counting closed tickets too), or the card links drop `closed` so each count equals its list. Apply it to every card at once.

## Notes

**2026-09-30T03:55:35.903149Z**

Starting work on this task.

**2026-09-30T04:04:24.290024Z**

Fixed in a9740f4. The overview ignores its own query string, as every other page does, so each card's link carries only its row's filter. Every count now equals the list its link opens, narrowed by the reader's tags alike. A filter in the overview's URL (closed=1, type, doc and the rest) is ignored rather than carried.

A new test follows every card's link and counts the rows, both with and without filters in the overview's URL. It failed on the filtered overview before the fix. Two older tests that asserted the carried filters were rewritten to the new rule.

The equality assumes a clean check: a terminal ticket knot has not archived is listed under its status but not counted among the closed, and the integrity card reports it.

Reviewed: brainstorm by the quality engineer (two rounds), spec and plan by their reviewers and the solution architect, and /code-review high with no findings. The brainstorm, spec and plan are attached as documents.
