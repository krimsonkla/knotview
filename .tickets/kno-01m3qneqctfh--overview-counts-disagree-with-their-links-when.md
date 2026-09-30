---
id: kno-01m3qneqctfh
title: Overview counts disagree with their links when the URL carries closed=1
status: open
type: task
priority: 2
mode: afk
created: '2026-09-29T22:44:35.353703Z'
updated: '2026-09-29T22:44:35.470181Z'
assignee: ''
---

The overview's "by" cards count live tickets, but each row's link carries the reader's selection, including `closed=1`. On `/?closed=1`, a row can say "chore 0" while its link lists a closed chore. The same happens on the "by document" card ("other 0" returns the closed ticket that owns an other). Found during the adversarial review of kno-01m3q9rs9632. It predates that story and affects every card.

## Design

Decide one rule for the whole overview. Either the counts follow `closed=1` (counting closed tickets too), or the card links drop `closed` so each count equals its list. Apply it to every card at once.