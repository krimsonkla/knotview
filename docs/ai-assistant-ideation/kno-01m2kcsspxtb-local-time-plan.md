# kno-01m2kcsspxtb — Local time implementation plan

**Goal:** every clock time on the panel reads in the reader's own zone, labelled, when the
browser can render it, and as labelled UTC when it cannot; distances are unchanged.

**Architecture:** the server keeps one rendering path and emits each instant as a `time`
element with knot's ISO instant on `datetime` and a labelled UTC text; a block in follow.js
restates `time.stamp` text in the browser's zone and adds a `title` to both kinds. Nothing is
written back and no zone state is kept. Spec: `kno-01m2kcsspxtb-local-time-spec.md`.

**Tech stack:** Jinja2 macros, one static script, pytest over `TestClient` with the
`DeclaredBacklog` fixture. Gate: `black`, `pytest` at 100 percent line and branch, `ruff`,
`pylint`, run inside `devenv shell -- <cmd>`.

**Commits:** one commit at `complete-task` carrying the work, the ticket transition and the
docs, per this repository's practice on `main`; each task below ends with the gate instead.

---

## Changes since last cycle

- The header's clauses are separate `span.when` elements and the middle dot moves to CSS
  (`.when + .when::before`), so a missing earlier clause never leaves a leading dot; a
  mixed-presence test covers it and `panel.css` joins the file list.
- The overview distance keeps its muted wrapper around the macro, since `time.ago` carries no
  dimming class of its own.
- The recently-closed card's cells are asserted once on the overview page.
- Line citations for `ticket.html` corrected; the import placement instruction names the
  physical line it lands on.

## Files

- Create: `src/knotview/panel/templates/_time.html` (two macros)
- Modify: `src/knotview/panel/templates/ticket.html:38-43` (header) and `:157-159` (notes)
- Modify: `src/knotview/panel/static/panel.css` (one rule for the header clauses)
- Modify: `src/knotview/panel/templates/_ticket_table.html:1` (import) and `:97` (cell)
- Modify: `src/knotview/panel/templates/overview.html:143` (recently changed row)
- Modify: `src/knotview/panel/static/follow.js` (header comment, third block)
- Modify: `README.md` "What it shows" table (one clause)
- Create: `tests/panel/test_follow.py`
- Modify: `tests/panel/test_ticket.py`, `tests/panel/test_tickets.py`,
  `tests/panel/test_overview.py`

## Task 1: The macros and the ticket header

**Files:** create `_time.html`; modify `ticket.html:38-43` and `panel.css`; test `tests/panel/test_ticket.py`.

- [ ] **Step 1: write the failing tests.** Replace the instant assertion in
  `test_the_header_carries_the_chips_the_instants_and_the_parent` and add one test:

```python
def test_the_header_carries_the_chips_the_instants_and_the_parent(client):
    page = client(DeclaredBacklog()).get("/ticket/pro-01m2bbbbbbbb").text

    assert "<h1>The child</h1>" in page
    assert 'href="/tickets?mode=afk"' in page
    assert "nobody" in page
    assert (
        'created <time class="stamp" datetime="2026-09-01T10:00:00.000000Z">2026-09-01 10:00 UTC</time>'
        in page
    )
    assert (
        'updated <time class="stamp" datetime="2026-09-04T10:00:00.000000Z">2026-09-04 10:00 UTC</time>'
        in page
    )
    assert '<a href="/ticket/pro-01m2aaaaaaaa">pro-01m2aaaaaaaa</a>' in page


def test_an_absent_instant_leaves_its_clause_out_and_emits_no_time_element(client):
    bare = ticket("pro-01m2eeeeeeee", created=None, updated=None)
    later = ticket("pro-01m2gggggggg", created=None)
    page = client(DeclaredBacklog(live_value=(bare,))).get("/ticket/pro-01m2eeeeeeee").text
    mixed = client(DeclaredBacklog(live_value=(later,))).get("/ticket/pro-01m2gggggggg").text

    header = page.split("<h1>")[1].split("</header>")[0]
    assert "created" not in header and "<time" not in page
    assert '<span class="when">updated <time' in mixed and "·" not in mixed.split("</header>")[0]
```

  The header markup no longer carries the middle dots (CSS draws them), so the assertions
  above check each clause on its own.

  And in `test_a_closed_ticket_shows_when_it_closed_and_an_assignee_is_a_link` change the
  closed assertion to
  `'closed <time class="stamp" datetime="2026-08-02T10:00:00.000000Z">2026-08-02 10:00 UTC</time>' in closed`.

- [ ] **Step 2: run them.** `devenv shell -- pytest --no-cov tests/panel/test_ticket.py -q`.
  Expected: the three touched tests fail on the missing `<time` markup.

- [ ] **Step 3: create `src/knotview/panel/templates/_time.html`:**

```jinja
{# An instant as the reader should see it. Both macros put knot's ISO instant on `datetime`,
   the one raw carrier, so follow.js can restate it in the browser's zone; the text is what a
   reader without script sees, and it names UTC so it cannot be read as local time. `stamp` is
   rewritten by the script; `ago` never is, only given a title. Callers guard on presence: an
   absent instant emits no element. An unparseable instant would read as garbage labelled UTC;
   knot owns the schema, so there is no guard for it. #}
{% macro stamp(instant) -%}
<time class="stamp" datetime="{{ instant }}">{{ instant | humanise }} UTC</time>
{%- endmacro %}
{% macro ago(instant) -%}
<time class="ago" datetime="{{ instant }}">{{ instant | ago }}</time>
{%- endmacro %}
```

- [ ] **Step 4: rewrite the header line in `ticket.html`** (the `<p class="muted">` at lines
  38-43) so each clause is its own guarded span and the separators come from CSS, so no
  combination of absent clauses leaves a stray dot:

```jinja
    <p class="muted">
      {% if ticket.created %}<span class="when">created {{ stamp(ticket.created) }}</span>{% endif %}
      {% if ticket.updated %}<span class="when">updated {{ stamp(ticket.updated) }}</span>{% endif %}
      {% if ticket.closed %}<span class="when">closed {{ stamp(ticket.closed) }}</span>{% endif %}
      {% if ticket.parent %}<span class="when">under
        <a href="/ticket/{{ ticket.parent }}">{{ ticket.parent }}</a></span>{% endif %}
    </p>
```

  Add to `panel.css`, next to the `.muted` rule:

```css
/* Clauses of the ticket header, separated by a dot only between two that are present. */
.when + .when::before {
  content: " · ";
}
```

  Add `{% from "_time.html" import stamp %}` as a new line 2 of `ticket.html`: line 1 holds
  the `extends`, the title block and the opening of the main block together, and the import
  works there. Update the two existing header assertions to the span form:
  `'<span class="when">created <time class="stamp" datetime="2026-09-01T10:00:00.000000Z">2026-09-01 10:00 UTC</time></span>'`
  and the same shape for updated and closed.

- [ ] **Step 5: run the tests again**, expected pass. Then the whole file with coverage off.

## Task 2: Note headings

**Files:** modify `ticket.html:157-159`; test `tests/panel/test_ticket.py`.

- [ ] **Step 1: failing test:**

```python
def test_a_dated_note_heading_is_a_stamp_and_an_undated_one_is_not(client):
    noted = ticket(
        "pro-01m2ffffffff",
        sections={"notes": "Written by hand.\n\n**2026-09-12T06:44:01.672814Z**\n\nSaid later."},
    )
    page = client(DeclaredBacklog(live_value=(noted,))).get("/ticket/pro-01m2ffffffff").text

    assert (
        '<time class="stamp" datetime="2026-09-12T06:44:01.672814Z">2026-09-12 06:44 UTC</time>'
        in page
    )
    assert "undated" in page and page.count("<time") == 3
```

  (three: created, updated, the one dated note.)

- [ ] **Step 2: run it**, expected fail on the missing `<time`.
- [ ] **Step 3: change the note heading** to

```jinja
        <h3 class="muted">
          {% if note.at %}{{ stamp(note.at) }}{% else %}undated{% endif %}
        </h3>
```

  (the `title` attribute goes.)
- [ ] **Step 4: run**, expected pass.

## Task 3: The table cell

**Files:** modify `_ticket_table.html:1` and `:97`; test `tests/panel/test_tickets.py`.

- [ ] **Step 1: failing tests.** Replace `test_the_instant_column_shows_whichever_order_is_on`:

```python
def test_the_instant_column_shows_whichever_order_is_on_as_a_stamp(client):
    by_updated = client(DeclaredBacklog(live_value=(CHILD,))).get("/tickets").text
    by_created = client(DeclaredBacklog(live_value=(CHILD,))).get("/tickets?order=created").text

    assert (
        '<td class="muted"><time class="stamp" datetime="2026-09-04T10:00:00.000000Z">'
        "2026-09-04 10:00 UTC</time></td>" in by_updated
    )
    assert (
        '<td class="muted"><time class="stamp" datetime="2026-09-01T10:00:00.000000Z">'
        "2026-09-01 10:00 UTC</time></td>" in by_created
    )
    assert 'title="updated"' not in by_updated and 'title="created"' not in by_created


def test_an_absent_instant_in_either_column_is_a_dash_and_no_time_element(client):
    bare = ticket("pro-01m2eeeeeeee", created=None, updated=None)
    by_updated = client(DeclaredBacklog(live_value=(bare,))).get("/tickets").text
    by_created = client(DeclaredBacklog(live_value=(bare,))).get("/tickets?order=created").text

    assert '<td class="muted">—</td>' in by_updated and "<time" not in by_updated
    assert '<td class="muted">—</td>' in by_created and "<time" not in by_created
```

- [ ] **Step 2: run them**, expected fail.
- [ ] **Step 3: edit `_ticket_table.html`.** First line of the file, before the existing
  comment: `{% from "_time.html" import stamp %}` (an include does not inherit the includer's
  imports, so the import lives here). Line 97 becomes:

```jinja
      <td class="muted">{% if ticket[when] %}{{ stamp(ticket[when]) }}{% else %}—{% endif %}</td>
```

- [ ] **Step 4: run**, expected pass. Also run `tests/panel/test_overview.py`,
  `test_queue.py`, `test_tree.py`: every page that includes the table still renders.

## Task 4: The overview distance

**Files:** modify `overview.html:143`; test `tests/panel/test_overview.py`.

- [ ] **Step 1: failing tests.** In
  `test_recently_changed_lists_live_tickets_newest_first_with_a_relative_time` replace the
  title assertion with

```python
    assert '<time class="ago" datetime="2026-09-04T10:00:00.000000Z">' in section
    assert "d ago</time>" in section
    assert 'title="2026-09-04T10:00:00.000000Z"' not in section
```

  and add

```python
def test_a_recently_changed_ticket_without_an_updated_instant_shows_a_dash(client):
    bare = ticket("pro-01m2eeeeeeee", title="Never saved", updated=None)
    page = client(DeclaredBacklog(live_value=(bare,))).get("/").text

    section = page[page.index("recently changed") : page.index("recently closed")]
    assert "Never saved" in section and '<span class="muted">—</span>' in section
    assert 'class="ago"' not in section


def test_the_recently_closed_cells_are_stamps(client):
    page = client(DeclaredBacklog()).get("/").text

    closed = page[page.index("recently closed") :]
    assert '<time class="stamp" datetime="2026-09-02T10:00:00.000000Z">' in closed
```

  (the closed fixture keeps the default `updated`, which is the column the table shows.)

- [ ] **Step 2: run**, expected fail.
- [ ] **Step 3: edit `overview.html`.** Add `{% from "_time.html" import ago %}` as a new line
  2 (line 1 holds the `extends` and the block opening together), and replace line 143 with

```jinja
      <span class="muted">{% if ticket.updated %}{{ ago(ticket.updated) }}{% else %}—{% endif %}</span>
```

  The muted wrapper stays because `time.ago` carries no dimming class of its own and
  `panel.css` has none for it; the distance and its em-dash fallback render at one weight.

- [ ] **Step 4: run**, expected pass.

## Task 5: The script

**Files:** modify `follow.js` (header and a third block); create `tests/panel/test_follow.py`.

- [ ] **Step 1: failing structural test**, `tests/panel/test_follow.py`:

```python
"""The page-side script, checked for the shape the templates rely on.

There is no JavaScript runtime in the toolchain, so this reads the file. It proves the
selectors are present and the distance branch never assigns text; it does not prove the
rewrite works, which is verified by hand in a browser and recorded on the ticket.
"""

from pathlib import Path

FOLLOW = Path("src/knotview/panel/static/follow.js").read_text()


def test_stamps_are_selected_by_class_and_distances_are_never_rewritten():
    assert 'querySelectorAll("time.stamp[datetime]")' in FOLLOW
    assert 'querySelectorAll("time.ago[datetime]")' in FOLLOW
    ago_branch = FOLLOW[FOLLOW.index('"time.ago[datetime]"') :]
    assert "textContent" not in ago_branch


def test_the_rewrite_is_a_restatement_and_says_so():
    assert "Intl.DateTimeFormat" in FOLLOW
    assert "restates" in FOLLOW
```

- [ ] **Step 2: run**, expected fail.
- [ ] **Step 3: amend the header comment** of follow.js. Replace the sentence "Nothing here
  renders anything, which is the point: there is one rendering path on the server, so what a
  reader sees after a change is exactly what they would see on a fresh visit." with:

```js
// Nothing here adds content: there is one rendering path on the server, so what a reader sees
// after a change is exactly what they would see on a fresh visit. The last block restates
// instants the server already put in the markup, in the reader's own zone; it invents nothing.
```

- [ ] **Step 4: append the block** at the end of follow.js:

```js
// Instants in the reader's own zone. The server writes every instant as UTC with the zone named,
// which is right for a page without script and wrong for a reader in Berlin. Each `time.stamp`
// is restated here in the browser's zone, in the same fixed shape so columns still line up, and
// the exact instant moves to the title. A `time.ago` keeps its distance text and only gains the
// title: the distance is the information on that card. The two are told apart by class, so the
// distance text cannot be rewritten by mistake.
(function () {
  if (typeof Intl === "undefined" || typeof Intl.DateTimeFormat !== "function") return;
  var zone = "";
  try {
    zone = Intl.DateTimeFormat().resolvedOptions().timeZone || "";
  } catch (e) {
    zone = "";
  }
  var shape = new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZoneName: "short",
  });
  var restated = function (when) {
    var parts = shape.formatToParts(when);
    var got = {};
    for (var i = 0; i < parts.length; i++) got[parts[i].type] = parts[i].value;
    var hour = got.hour === "24" ? "00" : got.hour;
    var text = got.year + "-" + got.month + "-" + got.day + " " + hour + ":" + got.minute;
    return got.timeZoneName ? text + " " + got.timeZoneName : text;
  };
  var title = function (element) {
    var raw = element.getAttribute("datetime");
    element.title = zone ? raw + " · " + zone : raw;
  };
  var stamps = document.querySelectorAll("time.stamp[datetime]");
  for (var s = 0; s < stamps.length; s++) {
    var when = new Date(stamps[s].getAttribute("datetime"));
    if (isNaN(when.getTime())) continue;
    stamps[s].textContent = restated(when);
    title(stamps[s]);
  }
  var distances = document.querySelectorAll("time.ago[datetime]");
  for (var d = 0; d < distances.length; d++) title(distances[d]);
})();
```

  The `"24"` check covers engines that render midnight as 24:00 under `hour12: false`.

- [ ] **Step 5: run**, expected pass. Run the prek hooks that touch js: `devenv shell -- prek
  run --all-files` (eclint, prettier) and fold any reformat.

## Task 6: README

**Files:** modify `README.md`, the "What it shows" table's Ticket row and the paragraph above
the table.

- [ ] **Step 1:** append to the paragraph that begins "The bar on every page holds the tags":
  a new paragraph, "Every instant is shown in your browser's timezone, labelled with it, and the
  exact UTC instant is on hover. Without script the page shows UTC, labelled as such."
- [ ] **Step 2:** no test; `prek` checks the markdown.

## Task 7: Gate, manual check, close

- [ ] **Step 1: the gate.** `devenv shell -- black src tests`, `devenv shell -- pytest` (100
  percent required), `devenv shell -- ruff check src tests`, `devenv shell -- pylint src tests`.
- [ ] **Step 2: manual verification.** Start a throwaway instance from the working tree on a
  free port (`.devenv/state/venv/bin/knotview --repository . --port 7799`), open a ticket page
  and the overview in Chrome, read the header stamp, hover it, read a distance. Record browser,
  zone and observed text for the closing note. Stop the instance.
- [ ] **Step 3: file the deferred ticket** for the since-last-looked precision bug through
  `create-story.sh`, and note its id in the closing note.
- [ ] **Step 4: `complete-task`** commits everything with the ticket's transition to done.

## Execution notes

**Drift, found at Task 7's manual check:** the browser served both `follow.js` and `panel.css`
from its cache (`deliveryType=cache`), so the page under test ran last hour's script under this
hour's markup and showed UTC with no separators. The static files are served with no cache
policy, so any reader restarting the panel after an upgrade would see the same. Fixed in place,
as the story's intent is unmet without it: `_asset_stamp` in `app.py` digests the static files
into a twelve-character stamp put on every static URL (`/static/follow.js?v=<stamp>`) through a
template global, so each version is a new URL. One test in `tests/panel/test_routes.py`; the two
existing assertions on the script URLs updated. Recorded on the ticket at close.
