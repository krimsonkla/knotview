---
id: kno-01m2ehjb39rh
title: '[P2] Formatter reflow left one-word lines in four docstrings'
status: open
type: task
priority: 2
mode: hitl
created: '2026-09-13T23:27:47.817579Z'
updated: '2026-09-13T23:27:47.939289Z'
assignee: ''
parent: kno-01m2ebf5sxdb
---

## Description
Pre-public audit finding, severity P2, from the review workflow over main at fcc6b66 on 2026-09-13. Raised by the hygiene lens and confirmed by an adversarial verifier.

### From the hygiene lens: Formatter-reflow artefacts leave one-word lines in four docstrings

Evidence: src/knotview/reading/knot_command.py:96-98 "...would\n        hide\n        the very thing"; :172-174 "output that will\n    not parse is\n    a different thing"; src/knotview/panel/selection.py:140-141 "tickets\n        whose\n        titles"; :157-158 "by hand\n    and\n    by link". ruff/pylint pass (100-char limit), so the hooks will not catch them.

Recommendation: Re-wrap those four paragraphs by hand; they are the only places the otherwise careful prose reads as broken.

Verifier (P2, blocks public: no): Reproduced verbatim: src/knotview/reading/knot_command.py lines 96-98 ("would / hide / the very thing") and 172-174 ("output that will / not parse is / a different thing"), and src/knotview/panel/selection.py lines 140-141 ("tickets / whose / titles") and 157-158 ("by hand / and / by link") each contain a one-word or fragment line mid-paragraph, the signature of a reflow after an edit. `ruff check` on both files reports "All checks passed!" and the configured line-length/max-line-length is 100 (pyproject.toml, .pylintrc), so no hook will surface them; only a hand re-wrap fixes it. It is cosmetic docstring prose with no behavioural or API effect, so P2 and not a blocker for going public is the right call.
