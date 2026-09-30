---
id: kno-01m3qneqctfh-dter2
ticket: kno-01m3qneqctfh
title: Overview counts brainstorm
type: other
created: '2026-09-30T04:04:23.400214Z'
updated: '2026-09-30T04:04:23.400214Z'
---

# Overview counts brainstorm

Story: kno-01m3qneqctfh. Date: 2026-09-30. Mode: teams-equivalent, quality-engineer challenger.

## Problem

The overview's cards count tag-narrowed tickets and ignore the URL, but their links carry every
filter the URL holds, so a count and the list it opens disagree whenever the overview's URL has a
filter: closed=1 in the ticket, and equally type, status, doc, assignee, q and the rest.

## Approach

The overview ignores its query string, as every other page does: it passes a bare `Selection()`.
Each card's link then carries only the filter that row means, and the tag cookie narrows the
counts and the lists alike, so each count equals its list by construction. A filter in the
overview's URL is silently ignored, as a stale bookmark's unknown value already is. The terminal
rows keep `closed=1&status=X`, now built from a bare selection because that is what those rows
mean. The docstring's claim that the overview narrows a filtered reader further goes, since no
link reaches it with a filter and it was the reasoning that produced the bug.

## Rejected

Counts following the whole selection: correct, but a deep text search would need a full read of
every ticket to count, and it keeps the overview unlike every other page.

## What the challenger changed

Tests for the class of filters, not closed=1 alone; a test that follows each card's link and
counts the rows; the docstring as part of the fix; the clean-check assumption stated; the tables'
inherited behaviours named; link shapes asserted exactly.
