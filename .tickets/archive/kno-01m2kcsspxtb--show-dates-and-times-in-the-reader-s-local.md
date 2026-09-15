---
id: kno-01m2kcsspxtb
title: Show dates and times in the reader's local timezone
status: closed
type: task
priority: 2
mode: afk
created: '2026-09-15T20:40:41.437116Z'
updated: '2026-09-15T21:33:01.154190Z'
closed: '2026-09-15T21:33:01.154190Z'
assignee: Jason Risch
acceptance:
- title: Every created, updated, closed and note instant on the ticket page, the tickets table, and the overview cards is a `time` element carrying the ISO instant on `datetime`
  done: true
- title: With script, the visible text is the instant in the browser's timezone and locale, and the exact UTC instant is on hover
  done: true
- title: Without script, the visible text names the zone (UTC) so it cannot be read as local time
  done: true
- title: The `ago` distances are unchanged
  done: true
- title: Tests cover the rendered `time` elements and the fallback text; coverage stays at 100 percent
  done: true
---

## Description

knot writes every instant as a UTC ISO timestamp, and the panel shows it as written: the `humanise` filter trims `2026-09-14T14:30:12.345Z` to `2026-09-14 14:30` and drops the Z, so the reader sees a UTC wall-clock time with no sign that it is UTC. A reader in another timezone reads a wrong time of day, and near midnight a wrong date. The ticket page (created, updated, closed, each note), the ticket table's created/updated column, and the overview's recently changed rows all show instants this way.

## Design

The server does not know the reader's timezone and must not guess one from the machine it runs on, because the panel is served on loopback but the browser may be on another machine or the machine's zone may differ from the reader's. So the server keeps emitting the instant, machine-readable, and the browser renders it. Two kinds of `time` element, chosen by class: `time.stamp` for created, updated, closed and dated-note instants, whose text follow.js rewrites into the browser's zone in the fixed shape `YYYY-MM-DD HH:MM` plus a zone label; and `time.ago` for the overview's distance, whose text the script never touches. Both carry knot's ISO instant on `datetime`, which is the only raw carrier in the fallback; the script adds a `title` with the exact UTC instant and the IANA zone. Without script, `time.stamp` reads `YYYY-MM-DD HH:MM UTC`. An absent instant emits no `time` element: "undated" and the em dash stay as today. The `ago` filter is unchanged.

Read the acceptance criteria with these two rewordings, which knot's criteria field cannot carry after creation: criterion 2 means "with script, the visible text is the instant in the browser's timezone in the fixed shape `YYYY-MM-DD HH:MM` followed by a zone label (whatever the engine gives, `CEST` or `GMT+2`), and the exact UTC instant with the IANA zone is on hover"; criterion 5 means "automated tests cover the emitted `time` elements, the fallback text, the class split and a structural check that follow.js selects `time.stamp` and not `time.ago`; coverage stays at 100 percent; the rewrite itself is verified manually in a browser set to a non-UTC zone, and the closing note records the browser, the zone and the observed text".

Known limits, accepted: local time without script is a non-goal, the reader sees labelled UTC. A brief UTC flash on first load is expected, since follow.js loads at the end of the body. The structural check proves the selector is present, not that the rewrite works; a later edit that breaks the rewrite while keeping the selector passes green.

## Notes

**2026-09-15T21:32:20.834745Z**

Implementation artifacts attached
branch: main commit: cd08d5576f182035fc3aa995002549288360b994
- Brainstorm: docs/ai-assistant-ideation/kno-01m2kcsspxtb-local-time-brainstorm.md @ cd08d5576f182035fc3aa995002549288360b994
- Spec: docs/ai-assistant-ideation/kno-01m2kcsspxtb-local-time-spec.md @ cd08d5576f182035fc3aa995002549288360b994
- Plan: docs/ai-assistant-ideation/kno-01m2kcsspxtb-local-time-plan.md @ cd08d5576f182035fc3aa995002549288360b994

**2026-09-15T21:32:49.692661Z**

Task completed: every instant is a `time` element with knot's ISO instant on `datetime` and `title`; the fallback text reads `YYYY-MM-DD HH:MM UTC`; follow.js restates `time.stamp` text in the browser's zone in the same shape with a zone label and puts the instant and the IANA zone on the title; `time.ago` keeps its distance text. Only a full Z-marked instant becomes a `time` element (`_is_instant`): a bare date or a word above a hand-written note is shown as written. Static URLs carry a content stamp (`?v=`), added when the manual check found the browser serving last hour's script and stylesheet from cache; without it a reader restarting the panel after an upgrade would keep the old script.

Verified by hand in Chrome with the machine in America/Los_Angeles (PDT), on a throwaway instance from the working tree: the ticket header read `created 2026-09-15 13:40 PDT · updated 2026-09-15 13:59 PDT`, hover `2026-09-15T20:40:41.437116Z · America/Los_Angeles`; the overview's `5 min ago` text was untouched with the same kind of title; a table cell read `2026-09-14 07:30 PDT`; both static files fetched from the network under the stamped URL. Chrome only: other engines accept the six-digit fractional seconds knot writes today, and a parse failure degrades to the labelled UTC text. The automated tests cover the emitted elements, the fallback text, the class split, the presence and shape guards and a structural check of follow.js; that check proves the selectors and the single text assignment are present, not that the rewrite works.

Deferred to kno-01m2ketsjym9: the since-last-looked block compares a millisecond instant against microsecond ones as strings, pre-existing. An earlier body edit on this ticket replaced the whole body and dropped the "Starting work on this task." note; the work started at 2026-09-15T20:51Z.

**2026-09-15T21:33:00.527423Z**

Acceptance criteria ticked as verified: Every created, updated, closed and note instant on the ticket page, the tickets table, and the overview cards is a `time` element carrying the ISO instant on `datetime`, With script, the visible text is the instant in the browser's timezone and locale, and the exact UTC instant is on hover, Without script, the visible text names the zone (UTC) so it cannot be read as local time, The `ago` distances are unchanged, Tests cover the rendered `time` elements and the fallback text; coverage stays at 100 percent
