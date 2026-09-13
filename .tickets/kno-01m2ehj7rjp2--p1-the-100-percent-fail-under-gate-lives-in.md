---
id: kno-01m2ehj7rjp2
title: '[P1] The 100 percent fail-under gate lives in pytest addopts, so any partial run exits 1 with green tests and nothing documents it'
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:44.401890Z'
updated: '2026-09-13T23:27:44.515185Z'
assignee: ''
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P1, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the tests lens and confirmed by an adversarial verifier.

### From the tests lens: The 100% fail-under gate lives in pytest addopts, so any partial run exits 1 with green tests and nothing documents it

Evidence: pyproject.toml [tool.pytest.ini_options] addopts = "--cov=knotview --cov-report=term-missing --cov-fail-under=100". `devenv shell -- pytest -q tests/values/test_ticket.py` prints `3 passed in 0.10s` followed by `FAIL Required test coverage of 100% not reached. Total coverage: 11.82%` and exits 1. Neither README.md (no testing section at all) nor CLAUDE.md ("Build & Test" is just `pytest`) mentions the gate, branch coverage, the `slow` marker, or how to run a subset. A first PR from a stranger who runs one file, or adds one untested branch, sees a coverage failure with no guidance.

Recommendation: Document in README/CONTRIBUTING: the gate is 100% line and branch; run a subset with `pytest --no-cov path`; run without knot with `-m "not slow"`. Consider moving --cov-fail-under out of addopts into the hook/CI invocation so plain `pytest <file>` stays green.

Verifier (P1, blocks public: no): Reproduced exactly as reported. pyproject.toml lines 49-59 set addopts = "--cov=knotview --cov-report=term-missing --cov-fail-under=100" with branch = true and a `slow` marker; `devenv shell -- pytest -q tests/values/test_ticket.py` prints `3 passed in 0.10s` after `FAIL Required test coverage of 100% not reached. Total coverage: 11.82%` and exits 1, while `pytest -q --no-cov tests/values/test_ticket.py` exits 0. README.md (56 lines, sections: What it shows / How it reads / Why not `knot serve`) has no testing content at all; CLAUDE.md's Build & Test is only `pytest` and `pre-commit run --all-files`; there is no CONTRIBUTING file, no .github/workflows, and devenv.nix/.pre-commit-config.yaml wire only ruff/pylint hooks, so nothing anywhere documents the gate, branch coverage, the `slow` marker, or `--no-cov`. The gate has been in addopts since the initial commit (d42c924) and is distinct from today's coverage-to-100% story (88731d9), which raised coverage to meet it rather than changing how it is invoked. P1 is fair because a first outside contributor running one file hits a red exit immediately with green tests; but it does not block going public: the failure message itself names the cause and the 100% threshold, `--no-cov` is the standard pytest-cov escape, and the fix is a short testing paragraph in README (or moving the threshold to the hook/CI invocation), which can land after publication without affecting any user of the tool.
