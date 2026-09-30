---
id: kno-01m2pqfrhmf5
title: 'Harden CI: pin the babashka, bbin and knot installs, and scope the workflow token'
status: closed
type: chore
priority: 2
mode: hitl
created: '2026-09-17T03:45:10.196021Z'
updated: '2026-09-30T03:28:45.299111Z'
closed: '2026-09-30T03:28:45.299111Z'
assignee: Jason Risch
---

## Notes

**2026-09-30T03:28:44.271974Z**

Already done in 3eb9511, "chore(ci): pin the babashka, bbin and knot installs, and scope the token", which named this ticket but did not close it. Checked against .github/workflows/ci.yml on main at c588f3d:
- babashka's installer is fetched from tag v1.13.223 and checked against a recorded SHA-256, and its release tarball against a second digest.
- bbin is fetched from v0.2.5 and checked the same way.
- knot is installed by commit sha (9956d45, v0.15.0) rather than by a tag, and a step asserts `knot --version` is 0.15.0.
- Every action is pinned by commit.
- The workflow token is scoped to `permissions: contents: read` at the top level.

Nothing remains to change.
