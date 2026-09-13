---
id: kno-01m2ehj5xney
title: '[P1] Ordinary CLI failures print Python tracebacks instead of the refusal page''s advice'
status: closed
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:42.517557Z'
updated: '2026-09-13T23:35:36.074473Z'
closed: '2026-09-13T23:35:36.074473Z'
assignee: Jason Risch
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P1, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the docs, security lenses and confirmed by an adversarial verifier.

### From the docs lens: Without knot on PATH the CLI crashes with a Python traceback whose advice tells the user to use a devenv shell they do not have

Evidence: Run from the scratchpad venv with knot hidden: `knotview --repository <dir>` prints a full traceback ending `knotview.values.unreadable_backlog.UnreadableBacklog: knot is not on the path. run this inside the devenv shell, where the tickets layer supplies knot`. src/knotview/reading/knot_command.py:147-150 hard-codes that devenv-specific advice; src/knotview/entry/console.py:97-98 calls `backlog.project()` in `main()` with no handler for UnreadableBacklog (or UnknownProject), so the friendly message/advice is buried in a stack trace instead of printed to stderr with a non-zero exit.

Recommendation: Catch UnreadableBacklog/UnknownProject in console.main, print `message` and `advice` to stderr and return 1. Change the advice at knot_command.py:149 to something an outsider can act on, e.g. 'install knot and put it on PATH, or pass --knot /path/to/knot'.

Verifier (P1, blocks public: no): Reproduced: with the devenv venv python and PATH=/usr/bin:/bin, `main(['--repository', <empty dir>])` exits 1 with a full traceback ending `UnreadableBacklog: knot is not on the path. run this inside the devenv shell, where the tickets layer supplies knot`. Confirmed src/knotview/reading/knot_command.py:146-150 hard-codes that advice and src/knotview/entry/console.py:86-101 has no try/except around settings_for() or backlog.project(), and nothing in src/knotview/entry/ catches UnreadableBacklog or UnknownProject. Worse than the report states: the case main()'s own docstring names as the ordinary mistake ("being pointed at a directory that is not a knot project") also dumps a traceback (`knot info was refused: no project found at or above ...`) even with knot present, so the promise "or say why it cannot be read" is not kept. Two mitigating facts on severity: the exit code is already non-zero and the message/advice are the last line of the traceback, and README.md only ever documents running via `devenv shell -- knotview ...`, so the devenv advice is consistent with the documented install path. It is P1 (a first user pointing at the wrong directory sees a stack trace), but it is a presentation defect with no correctness, data, or safety consequence and a ~10-line fix, so I would not call it a hard block on going public; it should be fixed before or alongside the first outside contributor.

### From the security lens: Ordinary CLI mistakes print Python tracebacks instead of the refusal message

Evidence: /Users/krimsonkla/git/krimsonkla/knotview/src/knotview/entry/console.py lines 93-101: main() calls settings_for(), KnotCommand.project() and uvicorn.run() with no try/except, although its docstring (line 88) promises to 'say why it cannot be read'. Verified: `devenv shell -- knotview --repository /tmp` ends in `Traceback ... knotview.values.unreadable_backlog.UnreadableBacklog: knot info was refused: no project found at or above /private/tmp ...`; `knotview nosuch` ends in a traceback for UnknownProject. A first user pointing it at the wrong directory or a mistyped saved name hits this immediately. Running without knot on PATH raises the same class through the same unhandled path.

Recommendation: Catch UnreadableBacklog and UnknownProject in main(), print `message` and `advice` to stderr, and return a non-zero exit code; add tests for both exits.

Verifier (P1, blocks public: no): Reproduced at fcc6b66. /Users/krimsonkla/git/krimsonkla/knotview/src/knotview/entry/console.py lines 93-101 call settings_for(), KnotCommand.project() and uvicorn.run() with no try/except, and nothing else on the path catches UnreadableBacklog or UnknownProject (grep shows handlers only in panel/app.py for HTTP requests, and pyproject's script points straight at console:main). `devenv shell -- knotview --repository /tmp` ends in a full traceback terminating in `UnreadableBacklog: knot info was refused: no project found at or above /private/tmp. run the same knot command...`, `knotview nosuch` in a traceback for `UnknownProject: no project is saved as 'nosuch'...`, and `knotview --knot /nonexistent/knot` in a traceback for `UnreadableBacklog: /nonexistent/knot is not on the path...`; all three exit 1. tests/entry/test_console.py only asserts pytest.raises on settings_for, never main()'s exit behaviour, so the docstring's 'say why it cannot be read' promise is untested and unmet. Both exception classes already carry `message` and `advice` fields, so the recommended fix is a few lines. I rate it P1 because a first outside user running it in the wrong directory or outside devenv hits it on their very first command, but it does not block going public: the exit code is already non-zero, the last line of the traceback carries the exact refusal message and advice, no data or security exposure is involved, and the panel itself works correctly once pointed at a real project. It is a strong should-fix-before-announcing polish item rather than a gate.

### From the security lens: Hand-edited projects.toml crashes with a traceback

Evidence: README.md lines 43-44 invite editing `~/.config/knotview/projects.toml` by hand. /Users/krimsonkla/git/krimsonkla/knotview/src/knotview/entry/saved_projects.py line 64 calls `tomllib.loads` unguarded and line 47 indexes `entry["repository"]` / `int(entry["port"])` unguarded. Verified: a file containing `[x` gives `tomllib.TOMLDecodeError: Expected ']' ...` traceback; a table missing `repository` gives `KeyError: 'repository'` traceback.

Recommendation: Wrap parsing and field access in SavedProjects and raise UnknownProject with the file path and advice; combine with the main() handler from the P1 finding so the user sees one line, not a stack.

Verifier (P2, blocks public: no): Confirmed by reproduction. I read /Users/krimsonkla/git/krimsonkla/knotview/src/knotview/entry/saved_projects.py: `_read` (line 64) calls `tomllib.loads` with no guard and `named` (line 47) does `entry["repository"]` / `int(entry["port"])` unguarded; the only place it is called is `main()` in src/knotview/entry/console.py, which has no exception handler at all. Running `main(['x'])` with XDG_CONFIG_HOME pointing at a scratch config produced: `[x` -> full traceback ending `tomllib.TOMLDecodeError: Expected ']' at the end of a table declaration (at line 1, column 3)`; a table missing `repository` -> `KeyError: 'repository'` traceback; `port = "abc"` -> `ValueError: invalid literal for int()` traceback (a third unguarded case the reporter did not list). The README invitation to hand-edit the file is real, though it is at README.md lines 21-22 ("plain TOML a person can edit"), not 43-44 as cited. Note the reporter's P1 sibling is what actually matters here: even the deliberately raised `UnknownProject` for an unknown name currently prints as a traceback because main() catches nothing, so this finding is largely subsumed by adding that handler. Severity P2 is right: it requires the user to corrupt their own config file by hand, the tomllib traceback already names the line and column, and nothing is exposed or damaged. Does not block going public.

## Notes

**2026-09-13T23:35:35.419167Z**

Task completed: main() catches UnreadableBacklog and UnknownProject, prints the message and the advice to stderr as two knotview: lines and exits 1; the missing-knot advice now says to install knot or pass --knot; SavedProjects refuses a malformed projects.toml and a table missing a field with the path and advice instead of a traceback. Four tests added; suite 149 at 100 percent.
