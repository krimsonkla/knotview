---
id: kno-01m2ehjfsgb8
title: '[P2] The live stream spawns a knot process every second per open tab and dies on a file-removal race'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:52.624032Z'
updated: '2026-09-13T23:43:38.621169Z'
closed: '2026-09-13T23:43:38.621169Z'
assignee: Jason Risch
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the security lens and confirmed by an adversarial verifier.

### From the security lens: /live spawns a knot process every second per open tab and dies on a file-removal race

Evidence: /Users/krimsonkla/git/krimsonkla/knotview/src/knotview/reading/knot_command.py line 514: digest() calls `self.project()`, i.e. `knot info --json` (a subprocess, ~0.09 s wall per `time knot info --json`), then rglobs and stats every ticket file. app.py lines 182-196 call digest() every HEARTBEAT=1.0 s per connected stream, so N tabs = N subprocesses per second; the comment at app.py lines 20-22 describes the check as only 'a directory walk over small files', which is not what runs. Lines 518-121 call `path.stat()` on each rglob result with no guard; `_changes` catches only UnreadableBacklog (line 188), so a ticket archived between rglob and stat raises FileNotFoundError, terminates the stream with a logged traceback, and the browser's EventSource reconnects (follow.js line 17). Starlette does stop the generator on client disconnect (StreamingResponse.listen_for_disconnect), so closed tabs do not leak.

Recommendation: Read tickets_path once (at KnotCommand construction or cached in digest) so the tick is pure filesystem work; wrap the stat in a try/except that skips vanished files; consider one shared watcher task publishing to all streams, and update the comment in app.py to match.

Verifier (P2, blocks public: no): Confirmed at fcc6b66, with corrected line numbers: KnotCommand.digest() at /Users/krimsonkla/git/krimsonkla/knotview/src/knotview/reading/knot_command.py:106-123 calls self.project() on every invocation, which goes through _read() (lines 137-145) and a synchronous subprocess.run of `knot info --json` (measured 0.112 s wall in this repo), then rglobs and calls path.stat() on each ticket file with no guard. /Users/krimsonkla/git/krimsonkla/knotview/src/knotview/panel/app.py:182-196 `_changes` calls backlog.digest() every HEARTBEAT=1.0 s (line 24) per open /live stream and catches only UnreadableBacklog, so a FileNotFoundError from a file moved by `knot archive`/`knot delete` between rglob and stat would escape, kill that generator with a traceback, and the browser's EventSource (follow.js line 17) would auto-reconnect after flashing "offline". The comment at app.py:20-22 ("a directory walk over small files") does not match what runs. An additional wrinkle the reporter did not mention: the subprocess runs synchronously inside an async generator, so each tick blocks the uvicorn event loop for ~0.1 s per tab. None of this is a security or data-integrity issue for a read-only, single-user local panel: one tab costs roughly one 0.1 s process per second, the race window is milliseconds and self-heals via reconnect, and the existing digest tests (tests/reading/test_knot_command.py:122-146) cover the intended behaviour. P2 polish, not a blocker; the recommendation (cache tickets_path, guard stat, fix the comment) is sound and cheap.

## Notes

**2026-09-13T23:43:37.941673Z**

Task completed: KnotCommand asks knot for the tickets directory once and keeps it, so the live stream no longer starts a knot process every second per open page; a file that vanishes between the directory listing and its stat is left out of that digest instead of raising. Both asserted through the fake.
