---
id: kno-01m2ehj4me4b
title: '[P1] A non-editable install ships without templates and static files, so pip install produces a broken command'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:41.198304Z'
updated: '2026-09-13T23:34:13.910384Z'
closed: '2026-09-13T23:34:13.910384Z'
assignee: Jason Risch
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P1, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the docs, packaging lenses and confirmed by an adversarial verifier.

### From the docs lens: A non-editable install ships without templates/ and static/, so `pip install .` produces a broken package

Evidence: Out-of-devenv test: `git archive HEAD` into the scratchpad, `uv pip install <copy>` exits 0, but `ls <venv>/site-packages/knotview/panel/` shows only `__init__.py app.py overview.py selection.py tree.py` — no templates/ or static/. Running the suite from that copy: `43 failed, 92 passed, 10 skipped`, every failure `RuntimeError: Directory '.../site-packages/knotview/panel/static' does not exist` raised from app.py:173 `app.mount("/static", StaticFiles(...))`, i.e. `panel()` itself cannot be constructed. Cause: pyproject.toml has only `[tool.setuptools.packages.find] where=["src"]` with no `package-data`/`include-package-data`, and there is no MANIFEST.in. It works locally only because devenv's `uv sync` installs editable.

Recommendation: Add `[tool.setuptools.package-data] knotview = ["panel/templates/*.html", "panel/static/*"]` (or `include-package-data = true` plus a MANIFEST.in), then re-run the install-from-archive test and the suite against the installed wheel before publishing.

Verifier (P1, blocks public: no): Reproduced independently: pyproject.toml at fcc6b66 has only [tool.setuptools.packages.find] where=["src"], no package-data/include-package-data, and no MANIFEST.in exists; `git archive HEAD` into the scratchpad then `uv build --wheel` produced knotview-0.0.0-py3-none-any.whl whose knotview/panel/ contains only the five .py files (templates/*.html and static/{follow.js,panel.css}, all git-tracked under src/knotview/panel/, are absent), and installing that wheel into a fresh venv confirms `(Path(app.__file__).parent/'static').exists()` is False, so `panel()` at app.py:173 (`app.mount("/static", StaticFiles(directory=str(HERE / "static")))`) cannot construct and the console script is unusable from any non-editable install. It works locally only because devenv.nix runs `uv sync` (editable). I rate it P1 rather than P0 because the README's sole documented install path is `devenv shell -- knotview ...`, there is no PyPI publish workflow (.github/workflows has none) and version is 0.0.0, so a first outside user following the docs does not hit it; but any contributor or user who does `pip install .`, `uv tool install`, or `uvx` from the repo gets a package that crashes on first use, and since pyproject advertises a console script and PyPI classifiers, the fix (`[tool.setuptools.package-data] knotview = ["panel/templates/*.html", "panel/static/*"]`, then rebuild and re-check the wheel) should land before any wheel or PyPI release is made.

### From the packaging lens: `pip install .` produces a knotview command that crashes: templates and static files are not packaged

Evidence: `uv build` then `unzip -l knotview-0.0.0-py3-none-any.whl` lists 22 .py files and no `knotview/panel/templates/*.html` or `knotview/panel/static/*` (sdist has 40 entries, none matching templates|static). Installing the wheel into a fresh `uv venv` and running `knotview --repository /Users/krimsonkla/git/krimsonkla/knotview --port 7799` prints the banner then: `RuntimeError: Directory '.../site-packages/knotview/panel/static' does not exist` raised from /Users/krimsonkla/git/krimsonkla/knotview/src/knotview/panel/app.py:173 (`app.mount("/static", StaticFiles(directory=str(HERE / "static")))`); templates at app.py:171 would fail the same way. It only works today because devenv installs the project editable (uv.lock: `source = { editable = "." }`).

Recommendation: In pyproject.toml add `[tool.setuptools.package-data] knotview = ["panel/templates/*.html", "panel/static/*"]` (or a MANIFEST.in with `include-package-data`), rebuild, and add a packaging smoke test/CI step that builds the wheel, installs it into a clean venv and requests `/` so this cannot regress.

Verifier (P1, blocks public: no): Reproduced end to end. pyproject.toml uses setuptools with only [tool.setuptools.packages.find] where=["src"], no package-data or include-package-data, and there is no MANIFEST.in, while src/knotview/panel/templates/ (10 .html) and src/knotview/panel/static/ (panel.css, follow.js) exist on disk and app.py:171-173 resolves them via HERE / "templates" and HERE / "static". I ran `uv build` into the scratchpad: the wheel contains 22 .py files and zero entries matching templates|static, and the sdist likewise has none. Installing that wheel into a fresh `uv venv --clear` and running `knotview --repository <repo> --port 7799` crashes with `RuntimeError: Directory '.../site-packages/knotview/panel/static' does not exist` from starlette's StaticFiles.__init__, exactly as reported; the editable install via devenv/uv.lock is why it works locally. On severity: the finding is real and a `pip install`/`uv tool install` user hits it on first run, but the README documents only `devenv shell -- knotview ...` (an editable checkout), the version is 0.0.0 with no publish/release workflow, and nothing tells outside users to install from a built artifact, so it is a first-contributor/first-packager hazard (P1) rather than a must-fix-before-any-public-visibility P0. The recommended fix (package-data entry plus a build-install-smoke test) is correct and cheap, and should land before any wheel or PyPI release is advertised.

## Notes

**2026-09-13T23:34:13.255212Z**

Task completed: the wheel now carries panel/templates/*.html and panel/static/* via [tool.setuptools.package-data]; verified by building the wheel, installing it into a fresh venv outside the checkout and serving / and /static/panel.css from the installed package.
