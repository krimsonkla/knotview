---
id: kno-01m2ehjgepjn
title: '[P2] A ticket identifier starting with a dash is handed to knot''s option parser'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:53.302300Z'
updated: '2026-09-13T23:43:03.907141Z'
closed: '2026-09-13T23:43:03.907141Z'
assignee: Jason Risch
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the security lens and confirmed by an adversarial verifier.

### From the security lens: Ticket identifier from the URL is handed to knot's option parser when it starts with '-'

Evidence: /Users/krimsonkla/git/krimsonkla/knotview/src/knotview/reading/knot_command.py line 562: `_spoken` builds `[knot, "show", identifier, "--json"]` with no validation and no `--` separator (knot 0.12.0 does not honour `--`: `knot show -- --help --json` still prints usage). `GET /ticket/--help` therefore runs `knot show --help --json`, which prints usage text and yields the 503 unreadable page; `-x` yields 'Unknown option'. No traversal: FastAPI rejects an encoded slash (404) and `knot show ../../etc/passwd --json` returns a not_found envelope. argv is a list, so no shell metacharacters reach a shell.

Recommendation: Reject identifiers that do not match a conservative id pattern (e.g. `^[A-Za-z0-9][A-Za-z0-9-]*$`) with the existing unknown.html page before spawning, and add a route test for `/ticket/--help`.

Verifier (P2, blocks public: no): Confirmed, with the location corrected: `_spoken` is at /Users/krimsonkla/git/krimsonkla/knotview/src/knotview/reading/knot_command.py line 159-164 (the file is 209 lines, not 562), and it returns `[self._knot, command, *arguments, "--json"]` with no validation and no `--`; `Pages.ticket` in src/knotview/panel/app.py:120 passes the path segment straight to `backlog.ticket(identifier)`. Against the real knot 0.12.0 in the devenv I reproduced every piece of evidence: `knot show --help --json` and `knot show -h --json` print usage (exit 0), `knot show -- --help --json` still prints usage so `--` would not fix it, `-x`/`--repo`/`--version` give "Unknown option", and `../../etc/passwd` returns a not_found envelope. Through a TestClient over `panel(KnotCommand(repository=<repo>))`, `GET /ticket/--help` and `/ticket/-x` both yield the 503 unreadable page ("knot show --help --json printed nothing this panel can read: USAGE"), while `/ticket/..%2F..%2Fetc%2Fpasswd` is a FastAPI 404. It is a real flaw, but the impact is small: `knot show` accepts only `--json` and `--no-color`, there is no flag that reads or writes outside the tickets dir, argv is a list so no shell is involved, subprocess has a timeout, and a plain unknown id like `/ticket/nope-000` already returns the same 503 page (tests/panel/test_ticket.py:45 documents that as current behaviour). So the worst outcome is a slightly more confusing 503 message for a hand-typed URL that no template ever links to. P2 polish, does not block going public; the recommended id-pattern guard plus a `/ticket/--help` route test is the right fix.

## Notes

**2026-09-13T23:43:03.292685Z**

Task completed: _spoken now hands knot the identifier after its end-of-options marker (knot show --json -- <id>), so an identifier starting with a dash is looked up rather than parsed as an option; asserted through the fake and through the real binary in the fidelity test.
