---
id: kno-01m2ketsjym9
title: Since-last-looked compares a millisecond instant against microsecond ones as strings
status: closed
type: task
priority: 2
mode: afk
created: '2026-09-15T21:16:11.230051Z'
updated: '2026-09-15T22:11:05.688970Z'
closed: '2026-09-15T22:11:05.688970Z'
assignee: Jason Risch
acceptance:
- title: A row saved in the same millisecond as the last look, later in it, is marked
  done: true
- title: The structural test in tests/panel/test_follow.py names the comparison
  done: true
---

## Description

The since-you-last-looked marking in `src/knotview/panel/static/follow.js` stores the last look as `new Date().toISOString()`, an instant to the millisecond ending in `Z`, and compares it as a string against each row's `data-updated`, which knot writes to the microsecond. For two instants sharing the same millisecond prefix, `Z` sorts above a digit, so a ticket saved within the same millisecond after the last look compares as older and goes unmarked.

## Design

Compare on a common precision: truncate both sides to the millisecond before comparing, or parse both with `Date.parse` and compare numbers. Sub-millisecond and pre-existing; raised by the quality-engineer during kno-01m2kcsspxtb and deferred as a separate mechanism.

## Notes

**2026-09-15T22:02:23.586322Z**

Starting work on this task.

**2026-09-15T22:11:03.581936Z**

Task completed: the since-last-looked block in follow.js pads the fractional seconds of both the stored last look and each row's `data-updated` to six digits before comparing the strings, so a row knot saved later in the same millisecond as the look is marked. The ticket's suggested `Date.parse` comparison was tried first and shown in JavaScriptCore to lose the difference, since a Date holds milliseconds: `.123456Z` and `.123Z` parse equal. Padding keeps knot's microseconds; the browser's millisecond look is zero-filled, which is the conservative side (a row saved earlier in that same millisecond is marked too, and after a click one such row can stay marked once more). Only knot's exact Z-marked shape is read; anything else compares as nothing, so a changed shape marks nothing rather than wrongly, and an unreadable stored look is replaced by now. Evidence from JavaScriptCore against a look of `…21:00:00.123Z`: same-millisecond-later true, next millisecond true, earlier false, no-fraction later true, junk null. The structural test in tests/panel/test_follow.py names the padding and the padded comparison and asserts neither the old string comparison nor Date.parse remains. Gate: 228 tests at 100 percent, ruff, pylint and hooks green.

**2026-09-15T22:11:04.554236Z**

Acceptance criteria ticked as verified: A row saved in the same millisecond as the last look, later in it, is marked, The structural test in tests/panel/test_follow.py names the comparison
