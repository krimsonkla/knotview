# kno-01m2kcsspxtb — Local time brainstorm

Story: kno-01m2kcsspxtb, "Show dates and times in the reader's local timezone". Date: 2026-09-15.
Mode: teams-equivalent, quality-engineer challenger, two rounds.

## Problem

knot writes every instant as a UTC ISO timestamp. The `humanise` filter in
`src/knotview/panel/app.py` trims `2026-09-14T14:30:12.345Z` to `2026-09-14 14:30` and drops the
Z, so the reader sees a UTC wall-clock time with nothing saying it is UTC. A reader in another
zone reads a wrong time of day, and near midnight a wrong date. Instants render in three places:
the ticket page (created, updated, closed, each dated note), the ticket table's created/updated
column, and the overview's recently-changed rows, which show a distance ("45 min ago") rather
than a clock time.

The server cannot know the reader's zone. It binds loopback, but the browser may be on another
machine, and the server machine's zone may differ from the reader's. The panel stays read-only.

## Prior art

`static/follow.js` is already the place where the page is enhanced after load: it follows the
`/live` stream and marks rows saved since the reader last looked, reading `data-updated` from
each row as an ISO string. Instants are therefore already emitted machine-readable for a script
to read, and the pattern of "server renders, script enhances, nothing is written back" is the one
to mirror. The `ago` filter is zone-free by construction and stays as it is.

## Approaches considered

1. **The browser renders each instant (chosen).** The server emits every instant as a `time`
   element carrying the ISO instant on `datetime`, with the trimmed UTC form as its text, zone
   named. A third block in follow.js rewrites the text into the browser's zone with
   `Intl.DateTimeFormat`. No cookie, no round trip, no state.
2. The browser stores its zone in a cookie, like the tag choice, and the server renders in it.
   Rejected: a cookie and a redirect for what is pure presentation, and the first page of every
   visit is still UTC.
3. A zone chosen in the URL or saved per project. Rejected: makes the reader manage what the
   browser already knows, and a saved zone is wrong the moment the reader travels.

## What the challenger changed

Round 1 raised three P0 and five P1 concerns; round 2 withdrew all but one, which stands as a
correction to the rationale. The design below is the revised one.

- **Two kinds of `time` element, chosen by class.** `time.stamp` for created, updated, closed
  and note instants: the script rewrites its text. `time.ago` for the overview distance: the
  script never touches its text, so the "45 min ago" the story says stays unchanged cannot be
  overwritten by construction. A blanket `time[datetime]` rewrite would have broken it.
- **A fixed shape, not the locale's.** `YYYY-MM-DD HH:MM <zone>` everywhere, before and after
  the rewrite. The instants sit in a sortable column and a timeline, where stable width and
  field order beat locale familiarity, and the shape matches the `datetime` a reader may copy.
  The ticket's second criterion said "timezone and locale"; it is reworded to timezone only.
- **The zone is always in the visible text**, so text alone is never mistakable and hover is an
  enhancement carrying precision rather than the only channel. The label is whatever Intl's short
  zone name yields, "CEST" or "GMT+2" alike; the criteria say "a zone label", never an
  abbreviation, so tests do not encode a platform-dependent name.
- **One raw carrier.** The fallback markup has no `title`; `datetime` holds the instant. The
  script adds `title` with the exact UTC instant and the IANA zone it rendered in. The table
  cell's current `title` (the column name) goes: the header already shows both names with the
  active one marked. A no-script reader hovering a note today sees the exact instant and will
  not after this; a small, accepted change.
- **Absent instants emit no element.** A note without a date still reads "undated"; a missing
  value still reads as an em dash. No `<time datetime="">` is ever emitted.
- **No-script local time is a non-goal.** Without script the reader sees UTC, labelled as such.
- **A brief UTC flash is expected on first load.** follow.js is an external script at the end of
  the body and browsers paint parsed content while it loads. Accepted; hiding the text with CSS
  until the rewrite would take it from no-script readers.
- **Verification is stated plainly.** There is no node in the toolchain, so the rewrite has no
  unit test. The automated tests cover the emitted elements, the fallback text, the class split,
  and a structural check that follow.js selects `time.stamp` and not `time.ago`. That check
  proves the selector is present, not that the rewrite works; a later edit that breaks the
  rewrite while keeping the selector passes green. The rewrite is verified manually in a browser
  set to a non-UTC zone, and the closing note records the browser, the zone and the observed
  text.

## Deferred

The since-last-looked comparison in follow.js compares a millisecond ISO string against knot's
microsecond instants, so a ticket saved within the same millisecond after the last look compares
as older and goes unmarked. Pre-existing and separate; filed as its own ticket at completion.
