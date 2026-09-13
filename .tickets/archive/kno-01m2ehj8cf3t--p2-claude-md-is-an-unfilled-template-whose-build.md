---
id: kno-01m2ehj8cf3t
title: '[P2] CLAUDE.md is an unfilled template whose Build and Test section contradicts the toolchain'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:45.039088Z'
updated: '2026-09-13T23:49:15.414080Z'
closed: '2026-09-13T23:49:15.414080Z'
assignee: Jason Risch
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the docs, hygiene, packaging, tests lenses and confirmed by an adversarial verifier.

### From the docs lens: CLAUDE.md is a stub with AI placeholder comments and two statements that are wrong

Evidence: CLAUDE.md lines 27-38: Architecture, Key Files, Local Conventions and Gotchas contain only `<!-- AI: ... -->` placeholders. Line 8 says 'Package Manager: pip' while the repo is uv-managed (uv.lock tracked, devenv.nix:15-22 `languages.python.uv.sync`). Lines 19-22 give `pytest` / `pre-commit run --all-files` with no note that both only work inside `devenv shell` (the pre-commit config is a gitignored Nix-generated symlink, .gitignore:5, so `pre-commit run` fails on a fresh clone). Line 14 lists `scripts/`, which is an empty directory (`ls scripts` -> nothing). It is the first file any AI-assisted outside contributor's tooling reads.

Recommendation: Either fill the four sections (the design in docs/ai-assistant-ideation and the module docstrings already contain the material: reading via `knot --json` only, READS constant guard, Pages/ROUTES assembly, loopback-only ADDRESS, digest-based /live) and fix the pip/uv and pre-commit statements, or delete the file rather than publish a template. Remove `scripts/` from the listing or the empty directory.

Verifier (P2, blocks public: no): The evidence reproduces, with off-by-a-few line numbers: /Users/krimsonkla/git/krimsonkla/knotview/CLAUDE.md line 11 says "Package Manager: pip" while uv.lock is tracked and devenv.nix:15-22 runs `uv sync` (no requirements.txt or pip lockfile exists); lines 28-42 (Architecture, Key Files, Local Conventions, Gotchas) hold only `<!-- AI: ... -->` placeholder comments; line 17 lists `scripts/`, which exists on disk but is empty and untracked by git (`git ls-files scripts` returns nothing, so it will not even exist in a fresh clone); lines 23-26 give `pytest` / `pre-commit run --all-files` with no devenv note, and .pre-commit-config.yaml is gitignored (.gitignore:5) and Nix-generated, so `pre-commit run` fails outside `devenv shell`. So the finding is real. However I downgrade it: CLAUDE.md is advisory tooling context, not user-facing docs or code; README.md already shows the correct `devenv shell -- knotview ...` invocation, so a contributor has an accurate entrypoint; the wrong "pip" line and the placeholders are embarrassing template residue that an AI-assisted contributor would notice but that does not break install, run, or tests. That is polish (P2) rather than something a first user hits as a failure, and it does not block going public — a five-minute fix (correct pip to uv, note devenv shell, drop `scripts/`, fill or delete the placeholder sections) is recommended before release but not a gate.

### From the hygiene lens: CLAUDE.md is an unfilled template that misdescribes the project

Evidence: CLAUDE.md:11 `Package Manager: pip` while devenv.nix:13-21 and uv.lock make uv the package manager; CLAUDE.md:17 lists `scripts/` but `ls scripts` shows an empty, untracked directory and `git ls-files` has no scripts entry; lines 28-42 are four headings each holding only an `<!-- AI: ... -->` placeholder comment. It is the first file an outside contributor's assistant reads.

Recommendation: Either fill it (uv, the src/knotview layout: entry/reading/panel/values, the read-only guard, `devenv shell -- pytest`, the templates-are-not-prettier gotcha) or delete it and the empty scripts/ directory before publishing.

Verifier (P2, blocks public: no): The evidence reproduces exactly: /Users/krimsonkla/git/krimsonkla/knotview/CLAUDE.md:11 says `Package Manager: pip` while devenv.nix:13-21 enables `languages.python.uv` with `uv sync` on shell entry, uv.lock exists, and nothing in pyproject.toml, devenv.nix or README.md mentions pip; CLAUDE.md:17 lists `scripts/` but `ls -la scripts` is empty, `git ls-files | grep '^scripts/'` returns 0 entries, and CLAUDE.md is the only file referencing it; lines 28-42 are four headings containing only `<!-- AI: ... -->` placeholders, and `git log -- CLAUDE.md` shows it was never touched after the initial commit (d42c924). However I would downgrade it from P1 to P2 and not treat it as a public blocker: README.md is accurate and substantive (correct `devenv shell -- knotview ...` invocation, description of the read-only panel), pyproject.toml is well-commented and correct, the FastAPI/pytest/devenv lines in CLAUDE.md are true, and the `pip` line is misleading but harmless (`pip install -e .` would still work against the setuptools pyproject). An outside contributor only sees CLAUDE.md if they use an AI assistant, and even then the worst outcome is being pointed at pip and a nonexistent scripts/ directory rather than a broken build. It is a hygiene/polish item worth fixing (fill it or delete it plus the empty scripts/), not something that must precede going public.

### From the packaging lens: CLAUDE.md contradicts the actual toolchain and is mostly empty

Evidence: /Users/krimsonkla/git/krimsonkla/knotview/CLAUDE.md lists `Package Manager: pip` while pyproject.toml uses `[dependency-groups]` and devenv.nix runs `uv sync` (`languages.python.uv.sync.enable = true`); its Build & Test block is `pytest` / `pre-commit run --all-files` with no note that both exist only inside `devenv shell`; the Architecture, Key Files, Local Conventions and Gotchas sections are empty headings.

Recommendation: Update CLAUDE.md (or fold it into a CONTRIBUTING.md) to say uv, list the devenv-vs-plain commands, and fill in or remove the empty sections before contributors read it.

Verifier (P2, blocks public: no): Reproduced in full: /Users/krimsonkla/git/krimsonkla/knotview/CLAUDE.md says "Package Manager: pip", while pyproject.toml declares dev deps under [dependency-groups] (a uv/PEP 735 construct), uv.lock is checked in, and devenv.nix sets languages.python.uv.sync.enable = true with a comment stating devenv runs `uv sync` on shell entry; its Build & Test block is bare `pytest` / `pre-commit run --all-files` with no devenv note (pytest resolves only to .devenv/state/venv/bin/pytest and pre-commit is not on the host PATH, so the commands fail outside `devenv shell`); and Architecture, Key Files, Local Conventions and Gotchas are empty headings holding only template `<!-- AI: ... -->` placeholders. However, README.md consistently uses `devenv shell -- knotview ...` and does not mention pip, and the file is explicitly an AI-assistant scaffold rather than contributor documentation, so a first outside user following the README is not misled; only someone reading CLAUDE.md as a contributor guide would be. That makes it a real polish defect, correctly rated P2 and not a blocker for going public.

### From the tests lens: CLAUDE.md's Build & Test does not match the environment: pre-commit is not installed (the runner is prek), and the package manager is uv, not pip

Evidence: CLAUDE.md lines 22-25: ```pytest\npre-commit run --all-files```; line 11: "Package Manager: pip". Inside the shell `command -v pre-commit` prints nothing ("pre-commit: NOT on PATH") while `prek --version` gives 0.4.14. devenv.nix enables `languages.python.uv` with `sync.enable = true`; there is no pip workflow and uv.lock is committed. CLAUDE.md's Architecture, Key Files, Local Conventions and Gotchas sections are empty placeholders ("<!-- AI: ... -->"). Hooks also enforce `conventional-commits` and `no-coauthor-trailers` (.pre-commit-config.yaml ids at lines 291 and 489) and `knot-check`, none of which are documented anywhere a contributor would read.

Recommendation: Correct CLAUDE.md (prek run --all-files; uv) and fill the empty sections, or replace it with a short CONTRIBUTING.md that lists: how to enter the environment, `pytest`, `prek run --all-files`, the conventional-commit rule, the no-co-author-trailer rule, and that knot must be on PATH for the fidelity test.

Verifier (P2, blocks public: no): The evidence reproduces exactly: CLAUDE.md (committed, last touched 2026-09-13) lists "Package Manager: pip" at line 11 and "pre-commit run --all-files" at line 25, while inside the devenv shell `command -v pre-commit` prints nothing and `prek --version` gives 0.4.14; uv 0.12.5 is on PATH, uv.lock is committed, no requirements*.txt exists, and devenv.nix lines 13-19 configure languages.python.uv with sync on shell entry. The Architecture/Key Files/Local Conventions/Gotchas sections are indeed empty "<!-- AI: -->" placeholders, and the conventional-commits (line 291), knot-check (line 423) and no-coauthor-trailers (line 489) hook ids are present in the generated .pre-commit-config.yaml, which is a gitignored symlink into /nix/store, so nothing committed documents them; no CONTRIBUTING.md exists and README.md mentions none of it. I downgrade the severity, though: CLAUDE.md is an AI-assistant memory file rather than the primary contributor entry point, README already documents `devenv shell` as the way in, and the hooks are installed automatically by devenv (`.git/hooks/pre-commit` and `commit-msg` are prek-generated and hardcode the prek store path), so a contributor who commits gets conventional-commit, no-coauthor and knot-check enforcement regardless of what CLAUDE.md says; the only concrete failure is a "command not found" on a stale one-liner, with the correct tool obviously on PATH. That is a genuine doc inaccuracy worth a two-line fix (prek, uv) plus a short contributor note, but it does not block going public. Separately noted, not part of this finding: devenv.yaml pulls `devenv-layers` from a git+ssh private GitHub URL, which is the thing that would actually stop an outside contributor from entering the shell at all.

## Notes

**2026-09-13T23:49:14.808963Z**

Task completed: CLAUDE.md is filled in from the code as it is (uv, prek, the reading port, Pages and ROUTES, the guards, the digest, key files, conventions, gotchas), and docs/ai-assistant-ideation/README.md says what those documents are and that the harness they mention is the maintainer's.
