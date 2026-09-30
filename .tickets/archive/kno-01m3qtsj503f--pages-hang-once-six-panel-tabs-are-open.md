---
id: kno-01m3qtsj503f
title: Pages hang once six panel tabs are open
status: closed
type: task
priority: 2
mode: afk
created: '2026-09-30T00:17:53.311827Z'
updated: '2026-09-30T00:38:47.325367Z'
closed: '2026-09-30T00:38:47.325367Z'
assignee: Jason Risch
tags:
- bug
---

Pages sometimes spin for a long time, reported while opening documents. Cause, reproduced in Chrome: every panel page holds a permanent `/live` server-sent-events connection, and a browser allows six HTTP/1.1 connections to one host. With six panel tabs open, the next request queues until a tab closes. Measured on a probe: a document page loaded in 742 ms, stalled past 8 s with six streams open, and loaded in 612 ms once they closed. Opening documents in new tabs reaches six quickly.

A second, smaller cause: the page handlers are `async def` but start knot synchronously, so a page's five or six knot reads (about 0.1 s each) block the event loop, and every other request and stream waits behind them.

## Design

Stop holding a connection per tab. Either:
- poll the existing `/digest` route about once a second, which is a short request and does the same work the stream does per tick; or
- keep one stream per browser, shared across tabs, through Web Locks and a BroadcastChannel.

Make the page handlers plain `def` so FastAPI runs them in its thread pool and one page's knot reads do not stall the rest.

## Notes

**2026-09-30T00:19:31.674166Z**

Starting work on this task.

**2026-09-30T00:38:46.731601Z**

Fixed in e1560bf.

Cause: each page held a /live stream, and Chrome allows six connections per host. The fix, in four parts:
- Pages poll /digest about once a second instead, and after their first answer a hidden tab stops polling until it is shown.
- Polling backs off to once every 30 s while the panel does not answer.
- Page handlers and refusal pages are plain functions, so knot runs in the thread pool.
- KnotCommand locks its cached paths.

Verified in Chrome:
- Nine polling pages open at once, with a page load at 0.6 to 0.9 s, where six streams had stalled it past 8 s.
- An edit reloaded all of them.
- A tab loaded while hidden reloaded when shown after a change.
- With a 2 s knot, /digest answered in 2 ms beside three loading not-found pages, where it had taken 11.9 s.

The developer confirmed a restart fixed the hangs. Reviewed by the quality engineer and the adversarial verifier; their two P1s and three P2s are fixed.
