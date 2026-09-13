---
id: kno-01m2ehj58mrp
title: '[P1] README has no install or prerequisites section and never says knot must be installed'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:41.844002Z'
updated: '2026-09-13T23:37:51.985985Z'
closed: '2026-09-13T23:37:51.985985Z'
assignee: Jason Risch
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P1, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the docs, packaging lenses and confirmed by an adversarial verifier.

### From the docs lens: README has no installation or prerequisites section: no pip/uv command, no Python version, no mention that knot must be installed

Evidence: `grep -n -E 'install|pip|uv |python|--knot' README.md` returns nothing. README.md never states `requires-python >=3.12` (pyproject.toml:9), never says knot 0.12.0 must be on PATH (knot_command.py:22 `KNOT = "knot"`, `knot --version` -> 0.12.0 in the dev shell) or links to how to install knot, and never mentions the `--knot` flag that console.py:50-52 provides for 'an unusual installation'. It links knot's repo once (line 3) but not as a prerequisite. pyproject.toml has no `[project.urls]`, `authors`, and `version = "0.0.0"`.

Recommendation: Add an 'Install' section to README: Python >=3.12, `uv sync` or `pip install .`, that `knot` (with the version tested) must be on PATH with a link to its install docs, and the `--knot` flag. Fill `authors`, `[project.urls]` and a real version in pyproject.toml.

Verifier (P1, blocks public: yes): Reproduced: `grep -n -i -E 'install|pip|uv |python|--knot' README.md` exits 1 with no matches; the README's only run instructions are `devenv shell -- knotview ...` and it never states a Python version (pyproject.toml line 9 has `requires-python = ">=3.12"`), never says `knot` must be on PATH (src/knotview/reading/knot_command.py:22 `KNOT = "knot"`, and the dev shell's knot is 0.12.0 from /nix/store), and never mentions the `--knot` flag at src/knotview/entry/console.py:51. pyproject.toml confirms `version = "0.0.0"`, no `authors`, no `[project.urls]`. The finding actually understates the problem: the one install path the README implies, `devenv shell`, depends on devenv.yaml input `git+ssh://git@github.com/krimsonkla/devenv-layers`, which `gh repo view` reports as PRIVATE, and knot itself is supplied only through that private layer's `[tickets] provider = "knot"` (devenv.config.toml). So a first outside user cannot follow the README at all: the devenv route fails on a private SSH input, and the plain-Python route (uv sync / pip install .) plus the knot prerequisite is undocumented. That is exactly the P1 definition (hit immediately by the first outsider) and it blocks going public in the sense that the repo is unusable from its README, though nothing here is a secret or legal blocker (not P0). docs/ contains only a coverage spec, no install guidance elsewhere.

### From the packaging lens: README offers no install or run path outside devenv, does not say knot must be installed, and the missing-knot failure is an uncaught traceback pointing at an internal 'tickets layer'

Evidence: /Users/krimsonkla/git/krimsonkla/knotview/README.md contains no pip/uv install instructions and no instruction to install knot; every command shown is `devenv shell -- knotview ...`. `knotview --knot /nonexistent/knot --repository .` inside the shell prints a full Python traceback ending `knotview.values.unreadable_backlog.UnreadableBacklog: /nonexistent/knot is not on the path. run this inside the devenv shell, where the tickets layer supplies knot` (raised at src/knotview/reading/knot_command.py:147; `main()` in src/knotview/entry/console.py:86-101 catches nothing). The 10 knot-driven tests skip with 'knot is not on PATH' (tests/reading/test_real_knot.py:16-19) when knot is absent, which is what every outside contributor will see.

Recommendation: Add Installation and Requirements sections to README (`pip install .` / `uv tool install`, Python >= 3.12, knot installed from https://github.com/UniSoma/knot and on PATH or passed via `--knot`), note that `pytest -m 'not slow'` / the skip behaviour, catch UnreadableBacklog in `main()` and print a one-line message with exit code 1, and reword the message to name knot's upstream instead of the devenv 'tickets layer'.

Verifier (P1, blocks public: yes): Reproduced. README.md has no Installation/Requirements section: every command is `devenv shell -- knotview ...`, and nothing says knot must be installed or how to get it (the only knot mention is a link in the first sentence); pyproject.toml declares requires-python >=3.12 and a `knotview` console script but the README never surfaces either. Running `devenv shell -- knotview --knot /nonexistent/knot --repository .` prints a full Python traceback ending `UnreadableBacklog: /nonexistent/knot is not on the path. run this inside the devenv shell, where the tickets layer supplies knot` (raised at src/knotview/reading/knot_command.py:147); grep of src/knotview/entry/ finds no reference to UnreadableBacklog, so main() in console.py:86-101 catches nothing despite its docstring promising to "say why it cannot be read". The advice text names a devenv-internal 'tickets layer', meaningless to anyone outside this repo's devenv config. tests/reading/test_real_knot.py:16-19 skips the real-knot tests when knot is absent, so an outside contributor's first `pytest` silently skips fidelity coverage. This is exactly what a first outside user hits on their first command, so P1 is right; not P0 because the tool still works once knot is installed and the exit code is 1.

## Notes

**2026-09-13T23:37:50.966757Z**

Task completed: README now leads with prerequisites (Python 3.12, knot on PATH or --knot, a knot project) and a plain uv/pip install and run path; the devenv shell is presented as the maintainer environment that depends on a private layer repository, with everything else runnable from uv sync --all-groups. The other half of this finding, making krimsonkla/devenv-layers public or switching the input from git+ssh, is the maintainer's decision and is left as is.
