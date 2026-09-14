---
id: kno-01m2emy9ykg0
title: Mark what changed since the reader last looked
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-14T00:26:45.587793Z'
updated: '2026-09-14T00:26:45.730987Z'
assignee: ''
---

## Description
The live stream tells the page when the digest moved and the page reloads, so what the reader sees is fresh but not informative: nothing says which tickets moved. The stream already carries the digest, and the browser can remember one.

## Design
Keep the last-seen digest and instant in the browser's own storage; after a reload mark rows whose updated instant is later than that instant, and show a small 'since you last looked' count in the bar that clears on click. Per-viewer state only, never sent to the server, which stays read-only.
