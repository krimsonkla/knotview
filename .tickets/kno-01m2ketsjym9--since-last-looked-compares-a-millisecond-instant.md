---
id: kno-01m2ketsjym9
title: Since-last-looked compares a millisecond instant against microsecond ones as strings
status: open
type: task
priority: 2
mode: afk
created: '2026-09-15T21:16:11.230051Z'
updated: '2026-09-15T21:16:11.404554Z'
assignee: ''
acceptance:
- title: A row saved in the same millisecond as the last look, later in it, is marked
  done: false
- title: The structural test in tests/panel/test_follow.py names the comparison
  done: false
---

## Description

The since-you-last-looked marking in `src/knotview/panel/static/follow.js` stores the last look as `new Date().toISOString()`, an instant to the millisecond ending in `Z`, and compares it as a string against each row's `data-updated`, which knot writes to the microsecond. For two instants sharing the same millisecond prefix, `Z` sorts above a digit, so a ticket saved within the same millisecond after the last look compares as older and goes unmarked.

## Design

Compare on a common precision: truncate both sides to the millisecond before comparing, or parse both with `Date.parse` and compare numbers. Sub-millisecond and pre-existing; raised by the quality-engineer during kno-01m2kcsspxtb and deferred as a separate mechanism.
