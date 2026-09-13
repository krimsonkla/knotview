---
id: kno-01m2ehjhrs5x
title: '[P2] Two third-party DeprecationWarnings on every test run are neither filtered nor explained'
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:54.648894Z'
updated: '2026-09-13T23:27:54.775004Z'
assignee: ''
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the tests lens and confirmed by an adversarial verifier.

### From the tests lens: Two third-party DeprecationWarnings on every run are neither filtered nor explained

Evidence: pytest output: `fastapi/testclient.py:1: StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead.` and `starlette/testclient.py:53: DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated, use anyio.from_thread.BlockingPortal instead.` Versions: starlette 1.6.0, fastapi 0.141.1, httpx 0.28.1 (pyproject dev group pins httpx>=0.27). No `filterwarnings` in [tool.pytest.ini_options].

Recommendation: Both originate in fastapi/starlette, not in this code. Either add `filterwarnings = ["ignore::DeprecationWarning:starlette.testclient", "ignore:Using .httpx. with .starlette.testclient.:DeprecationWarning"]` with a comment naming the upstream issue, or move the dev dependency to httpx2 once fastapi's TestClient supports it. Do not set `filterwarnings = error` without one of these, or the suite turns red on the next starlette bump.

Verifier (P2, blocks public: no): Reproduced: running `pytest -q` on main (fcc6b66) ends with "145 passed, 2 warnings" and the warnings summary shows exactly the two quoted warnings, both raised from site-packages (`fastapi/testclient.py:1` StarletteDeprecationWarning about httpx vs httpx2, and `starlette/testclient.py:53` DeprecationWarning about the anyio.abc.BlockingPortal alias), not from any file under src/ or tests/. `[tool.pytest.ini_options]` in pyproject.toml (lines 49-55) has testpaths, asyncio_mode, addopts (coverage) and markers but no `filterwarnings`, and the dev group pins `httpx>=0.27` with `fastapi>=0.115` unpinned upstream. So the finding is accurate, but it is purely upstream noise: the suite is green, nothing in the project code is deprecated, and no contributor is blocked or misled beyond two lines of console noise. P2 polish is the right severity; the recommendation (targeted filterwarnings entries with a comment, or moving to httpx2 when fastapi's TestClient supports it, and not setting filterwarnings=error) is sound and low-risk. Does not block going public.
