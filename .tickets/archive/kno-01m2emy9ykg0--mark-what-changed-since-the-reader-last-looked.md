---
id: kno-01m2emy9ykg0
title: Mark what changed since the reader last looked
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:45.587793Z'
updated: '2026-09-14T00:47:38.506776Z'
closed: '2026-09-14T00:47:38.506776Z'
assignee: Jason Risch
---

## Description
The live stream tells the page when the digest moved and the page reloads, so what the reader sees is fresh but not informative: nothing says which tickets moved. The stream already carries the digest, and the browser can remember one.

## Design
Keep the last-seen digest and instant in the browser's own storage; after a reload mark rows whose updated instant is later than that instant, and show a small 'since you last looked' count in the bar that clears on click. Per-viewer state only, never sent to the server, which stays read-only.

## Notes

**2026-09-14T00:47:37.856586Z**

Task completed: every ticket row carries its updated instant as a data attribute and the bar has a hidden 'since' element; follow.js keeps the instant of the reader's last page load in the browser's storage, marks rows saved after it, shows the count in the bar, and clicking the count makes now the last look. Per viewer only; nothing goes to the server.
