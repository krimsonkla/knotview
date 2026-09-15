# kno-01m2kcsspxtb — Local time spec

Story: kno-01m2kcsspxtb, "Show dates and times in the reader's local timezone". Date: 2026-09-15.
Brainstorm: `kno-01m2kcsspxtb-local-time-brainstorm.md`.

## Changes since last cycle

Implementation-review resolutions, all P2:

- Both macros carry `title="<instant>"` server-side as well as `datetime`, so a reader without
  script can still hover for the exact instant; the script overwrites the title with the zone it
  restated in. The "single carrier" point is withdrawn; the datetime is still the value the
  script reads.
- The macros guard on shape as well as the callers on presence: only a full, Z-marked instant
  becomes a `time` element (`_is_instant`, a Jinja test). A bare date or a word above a
  hand-written note is shown as written, never labelled UTC or restated. An instant with an
  offset is likewise shown as written rather than mislabelled.
- The asset stamp digests every file under the static folder recursively by relative path.
- follow.js also guards `formatToParts`.
- Verified in Chrome only; other engines accept six-digit fractional seconds today, and a parse
  failure degrades to the labelled UTC text.

## Problem

Every instant the panel shows is knot's UTC instant trimmed to `2026-09-14 14:30`, with nothing
saying it is UTC. A reader in another zone reads a wrong time of day, and near midnight a wrong
date.

## Goal

Every clock time on the panel reads in the reader's own zone, labelled with that zone, when the
browser can render it; and reads as labelled UTC, never as an unlabelled time, when it cannot.
Distances ("45 min ago") are unchanged. The panel writes nothing and keeps no zone state.

## Design

### The markup the server emits

Two macros in a new partial `src/knotview/panel/templates/_time.html`, imported where used:

```jinja
{% macro stamp(instant) -%}
<time class="stamp" datetime="{{ instant }}">{{ instant | humanise }} UTC</time>
{%- endmacro %}
{% macro ago(instant) -%}
<time class="ago" datetime="{{ instant }}">{{ instant | ago }}</time>
{%- endmacro %}
```

Two forms, both one `time` element with `datetime` set to knot's ISO instant exactly as written.

- `time.stamp`, text `2026-09-14 14:30 UTC`: the `humanise` filter's output with ` UTC`
  appended. Used for the ticket page's created, updated and closed instants and each dated note
  heading, and for the ticket table's created/updated cell.
- `time.ago`, text `45 min ago`: the `ago` filter's output. Used on the overview's
  recently-changed rows.

The fallback carries no `title`; `datetime` is the one raw carrier. Every call site, `ago`
included, guards on presence, since `Ticket.created`, `updated` and `closed` and `Note.at` are
all optional: a note without `at` still reads "undated"; a header clause (created, updated,
closed) whose instant is absent is omitted, as the closed clause already is; the table cell
branches, `{% if ticket[when] %}{{ stamp(ticket[when]) }}{% else %}—{% endif %}`; and a
recently-changed row whose ticket has no `updated` shows an em dash where the distance would be.
No `<time datetime="">` or `datetime="None"` is ever emitted.

The table cell loses its current `title="{{ when }}"`. The header already renders both column
names as sort links with the active one marked, so nothing is lost. The overview row's
`title="{{ ticket.updated }}"` and the note heading's `title="{{ note.at or '' }}"` go for the
same reason: the script sets a better title, and the fallback text already names the zone.

`humanise` and `ago` are unchanged. `humanise` still returns `—` for a missing value so the
callers that guard on presence keep their existing text.

### The script

A third block appended to `src/knotview/panel/static/follow.js`, in the file's existing style
(an IIFE, line comments, no dependencies):

1. Guard: return if `Intl` or `Intl.DateTimeFormat` is absent.
2. Resolve the zone once: `Intl.DateTimeFormat().resolvedOptions().timeZone` (the IANA name,
   may be undefined on old engines; then fall back to an empty label and skip the title's zone).
3. For every `time.stamp[datetime]`: parse `datetime` with `new Date(...)`; if invalid, leave
   the element alone. Otherwise set its text to `YYYY-MM-DD HH:MM <zone label>` built from
   `Intl.DateTimeFormat("en-CA", {year, month, day, hour, minute, hour12: false, timeZoneName:
   "short"}).formatToParts(date)`, assembling the parts so the shape is fixed regardless of
   locale (`en-CA` yields ISO-ordered numeric parts; the zone label is whatever the engine's
   short `timeZoneName` part gives, "CEST" or "GMT+2" alike). Set `title` to
   `<datetime> · <IANA zone>`.
4. For every `time.ago[datetime]`: never touch the text; set the same `title`.

The selector is by class, so the distance text cannot be rewritten by construction. The rewrite
runs after parse; a brief UTC flash on first load is expected and accepted.

### Where each instant renders

| Place | Element | Text with script | Text without |
|---|---|---|---|
| ticket page header: created, updated, closed | `time.stamp` | `2026-09-14 16:30 CEST` | `2026-09-14 14:30 UTC` |
| ticket page note heading, when dated | `time.stamp` | same | same |
| ticket table created/updated cell, when present | `time.stamp` | same | same |
| overview recently changed, when `updated` present | `time.ago` | `45 min ago` (hover: instant · zone) | `45 min ago` |
| overview recently closed, and every other card that includes the ticket table | `time.stamp` in the table cell | as the table | as the table |

### Out of scope

- Local time without script. The reader sees labelled UTC.
- Any zone choice by the reader, in the URL, a cookie or a saved project.
- The since-last-looked comparison precision in follow.js (filed separately at completion).

## Ticket edits

Criterion 2 becomes: "With script, the visible text is the instant in the browser's timezone in
the fixed shape `YYYY-MM-DD HH:MM` followed by a zone label, and the exact UTC instant with the
IANA zone is on hover."

Criterion 5 becomes: "Automated tests cover the emitted `time` elements, the fallback text, the
class split and a structural check that follow.js selects `time.stamp` and not `time.ago`;
coverage stays at 100 percent. The rewrite itself is verified manually in a browser set to a
non-UTC zone, and the closing note records the browser, the zone and the observed text."

The Design section gains: no-script local time is a non-goal; a brief UTC flash on first load is
expected; the structural check proves the selector is present, not that the rewrite works.

## Acceptance criteria

1. Every created, updated, closed and dated-note instant on the ticket page, every created or
   updated cell in the ticket table, and every recently-changed instant on the overview is a
   `time` element whose `datetime` is knot's ISO instant unchanged.
2. Criterion 2 as reworded above.
3. Without script, every `time.stamp` reads `YYYY-MM-DD HH:MM UTC`.
4. `time.ago` text is the `ago` filter's output, unchanged with or without script.
5. Criterion 5 as reworded above.
6. An absent instant emits no `time` element: "undated" and `—` remain as today.

## Testing strategy

Python, rendered-content assertions through the existing `client` fixture and `DeclaredBacklog`:

- `tests/panel/test_ticket.py`: the header renders three `time.stamp` elements with the
  declared instants on `datetime` and ` UTC` text; a ticket without `closed` renders two; a
  ticket without `created` or `updated` omits that clause; a dated note renders a `time.stamp`
  heading and an undated note renders "undated" with no `time` element.
- `tests/panel/test_tickets.py`: the when cell is a `time.stamp` for the ordered column and
  carries no `title`, for both `order=updated` and `order=created`; a ticket with no `updated`
  renders `—` and no `time` element in the updated column, and likewise for a ticket with no
  `created` in the created column, so both branches of the new conditional are covered.
- `tests/panel/test_overview.py`: a recently-changed row is `time.ago` whose text ends in
  "ago" or is "just now", with the instant on `datetime`; a live ticket without `updated` in
  that card shows an em dash and no `time` element; the recently-closed card's cells are
  `time.stamp` (covered by the table's own test, asserted once on the overview page).
- `tests/panel/test_live.py` or a new `tests/panel/test_follow.py`: reads
  `static/follow.js` and asserts it contains `time.stamp[datetime]` and `time.ago[datetime]`,
  and that the only text assignment happens inside the stamp loop (asserted as the `.ago`
  branch never assigning `textContent`; a structural check, stated as such).
- The `_humanise` and `_ago` unit tests are unchanged and must still pass.

Manual: open a ticket page from the running instance in Chrome with the machine in a non-UTC
zone, confirm the header reads the fixed shape with a zone label and the hover shows the ISO
instant and the IANA zone, confirm the overview's distance text is untouched; record browser,
zone and observed text in the closing note.

## Cross-story collision check

No high-risk-surfaces document exists under `_references/project/`; no scan performed. No other
open work touches these files.
