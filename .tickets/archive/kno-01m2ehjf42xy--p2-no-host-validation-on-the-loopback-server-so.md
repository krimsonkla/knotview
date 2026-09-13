---
id: kno-01m2ehjf42xy
title: '[P2] No Host validation on the loopback server, so DNS rebinding can read the whole backlog'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:51.938515Z'
updated: '2026-09-13T23:43:16.063591Z'
closed: '2026-09-13T23:43:16.063591Z'
assignee: Jason Risch
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the security lens and confirmed by an adversarial verifier.

### From the security lens: No Host validation on the loopback server (DNS-rebinding exposure of the whole backlog)

Evidence: /Users/krimsonkla/git/krimsonkla/knotview/src/knotview/panel/app.py lines 163-179 build the FastAPI app with no TrustedHostMiddleware; console.py binds 127.0.0.1 with no auth by design (lines 16-19). TestClient probe: `GET / ` with header `Host: evil.example` returned 200. A page on an attacker's domain whose DNS is rebound to 127.0.0.1:7778 can therefore read every ticket page from a viewer's browser. Same-origin policy blocks ordinary cross-origin reads; only rebinding is affected.

Recommendation: Add `app.add_middleware(TrustedHostMiddleware, allowed_hosts=["127.0.0.1", "localhost"])` in panel(), and note in README that the panel is intended for one reader on one machine.

Verifier (P2, blocks public: no): Reproduced. `panel()` in /Users/krimsonkla/git/krimsonkla/knotview/src/knotview/panel/app.py:163-179 adds only StaticFiles, an exception handler and the GET routes; grep over src/ finds no TrustedHostMiddleware, CORSMiddleware, Origin or Referer check anywhere. /Users/krimsonkla/git/krimsonkla/knotview/src/knotview/entry/console.py:16-23 hard-codes ADDRESS="127.0.0.1" and the comment explicitly states there is no authentication of any kind. My TestClient probe over tests.panel.declared.DeclaredBacklog returned 200 with full HTML (~6 KB) for `/` and `/tickets` with `Host: evil.example`, identical to `Host: localhost`, so a DNS-rebound page could indeed read every ticket page from a viewer's browser. However the surface is read-only (GET only, no mutating routes, no CORS headers so ordinary cross-origin reads are still blocked), the data is a project backlog rather than credentials, and the attack needs the victim to be running the panel and visit an attacker page while rebinding succeeds — the same posture as most local dev servers. P2 is the right rating; a one-line TrustedHostMiddleware plus a README sentence about loopback/one-reader intent is polish, not a public-release blocker.

## Notes

**2026-09-13T23:43:15.463656Z**

Task completed: panel() adds Starlette's TrustedHostMiddleware allowing 127.0.0.1, localhost and [::1]; a request for any other Host is answered 400 without touching the backlog, asserted in test_routes.py, and the test client now addresses 127.0.0.1.
