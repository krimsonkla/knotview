---
id: kno-01m3w61pvk11-dqnd3
ticket: kno-01m3w61pvk11
title: Epic children brainstorm
type: other
created: '2026-10-01T17:01:31.776592Z'
updated: '2026-10-01T17:01:31.776592Z'
---

# Epic children brainstorm

Story: kno-01m3w61pvk11, "On a ticket page, exclude closed children and order children by
status", the developer's request. Date: 2026-10-01. Mode: teams-equivalent, quality-engineer
challenger.

## Problem

On a long-running epic most children are closed, listed in knot's order among the open ones, so
the work still to do is buried.

## Approach

- **Order:** children, and the siblings card's tickets, sort by the project's declared status
  order. An undeclared status goes after the declared ones and a missing reference last; the sort
  is stable, so knot's order is kept within a status. Blocked by, blocking and linked keep knot's
  order: children are the relation an epic's page exists to show.
- **Hide closed:** `?children=live` hides children in a terminal status. Any other value shows
  everything. A link in the card's heading toggles it: shown, "children 7" with "hide closed (4)";
  hidden, "children 3 of 7" with "show closed". The card stays whenever it hid something, so an
  all-closed epic still offers the way back.
- **Values, not template logic:** `Pages.ticket` computes the children and siblings shown and
  their counts, so a number is counted from the rows it describes.
- **URL only, not carried:** the choice lives in this page's URL, and no other link on the page
  carries it.
- The tree's children are not reordered here.

## What the challenger changed

The card surviving an empty filtered list; one number for the count and the hidden total; values
computed in the page, which also fixes the siblings count's independent derivation; a defined place
for missing references; a fail-safe vocabulary; the other cards' order stated. Carrying the choice
between ticket pages was proposed and declined, as the carried-filter shape kno-01m3qneqctfh removed.
