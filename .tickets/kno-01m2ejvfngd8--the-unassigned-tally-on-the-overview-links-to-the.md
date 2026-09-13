---
id: kno-01m2ejvfngd8
title: The unassigned tally on the overview links to the unassigned tickets
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:50:15.984731Z'
updated: '2026-09-13T23:50:16.095536Z'
assignee: ''
---

## Description
Overview.by_queue carries an unassigned tally with filter=assignee and an empty value, which no URL can express because Selection.asked maps a blank assignee to any; overview.html renders it as a plain span. The count is right but cannot be followed.

## Design
Give Selection a spelling for 'nobody' (for example assignee=nobody) that matches tickets with no assignee, render the tally as a link to it, and keep the tickets page's filter summary reading naturally.
