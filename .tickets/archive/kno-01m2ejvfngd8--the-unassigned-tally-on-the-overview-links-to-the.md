---
id: kno-01m2ejvfngd8
title: The unassigned tally on the overview links to the unassigned tickets
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:50:15.984731Z'
updated: '2026-09-13T23:56:11.965800Z'
closed: '2026-09-13T23:56:11.965800Z'
assignee: Jason Risch
---

## Description
Overview.by_queue carries an unassigned tally with filter=assignee and an empty value, which no URL can express because Selection.asked maps a blank assignee to any; overview.html renders it as a plain span. The count is right but cannot be followed.

## Design
Give Selection a spelling for 'nobody' (for example assignee=nobody) that matches tickets with no assignee, render the tally as a link to it, and keep the tickets page's filter summary reading naturally.

## Notes

**2026-09-13T23:56:11.354075Z**

Task completed: the assignee filter has a word for nobody (assignee=nobody matches tickets with no assignee); the overview's unassigned tally carries that value and renders as a link like every other tally; asserted on both pages.
