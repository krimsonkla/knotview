---
id: kno-01m2ehjje0w7
title: '[P2] No task runner, and the dev dependency group does not match the hooks, so a non-devenv contributor has a different toolchain'
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:55.328628Z'
updated: '2026-09-13T23:27:55.455137Z'
assignee: ''
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the tests lens and confirmed by an adversarial verifier.

### From the tests lens: No task runner and the dev dependency group does not match the hooks, so a non-devenv contributor has a different toolchain

Evidence: No Makefile, justfile or Taskfile in git ls-files; devenv.nix defines no `tasks`/`scripts`; the only entry points are `devenv shell -- <cmd>`. pyproject.toml [dependency-groups] dev = pytest, pytest-cov, pytest-asyncio, httpx, pylint, black, but the enabled `ruff` hook (devenv.nix `git-hooks.hooks.ruff.enable = true`) uses nix ruff 0.16.3, which is not in the group, and `autoflake`, `prettier`, `eclint` run from nix as well. `uv sync --all-groups` outside devenv therefore cannot reproduce what the hooks will reject.

Recommendation: Add ruff to the dev group (pin close to the nix version) and provide a few devenv tasks or a justfile (test, lint, hooks, serve) so the workflow is one command and is the same inside and outside the shell.

Verifier (P2, blocks public: no): The evidence reproduces: `git ls-files` shows no Makefile/justfile/Taskfile and no CI workflow; /Users/krimsonkla/git/krimsonkla/knotview/devenv.nix defines no `tasks` or `scripts`, only `git-hooks.hooks.ruff.enable = true` and a pylint binPath override; pyproject.toml's `[dependency-groups] dev` is exactly pytest, pytest-cov, pytest-asyncio, httpx, pylint, black (no ruff, and uv.lock has no ruff entry); the generated .pre-commit-config.yaml (a symlink into /nix/store) runs ruff from `ruff-0.16.3` in the store plus autoflake, prettier, eclint, black 26.5.1 and ~25 other layer hooks from Nix paths, and README.md documents only `devenv shell -- ...` invocations. So a `uv sync --all-groups` outside devenv cannot run the ruff check the hook enforces. However the severity is correctly P2 and it does not block going public: the entire hook chain (not just ruff) is Nix-provided and comes from the devenv-layers input, so the repository already only supports the devenv path and never claims a non-devenv workflow; the missing ruff pin is a small consistency gap inside that, and a task runner is convenience. A contributor who enters the shell gets the same toolchain as the author, and anyone outside it is already unsupported for reasons far larger than one missing dev dependency. Recommendation (add ruff to the dev group, add a few devenv tasks) is reasonable polish.
