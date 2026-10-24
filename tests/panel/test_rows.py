"""One row per ticket, everywhere a list of tickets is shown, and the filters above them."""

import re
from pathlib import Path

from knotview.values.document import Document
from tests.panel.declared import DeclaredBacklog, ticket

STATIC = Path("src/knotview/panel/static")
TAGGED = ticket(
    "kno-r1",
    type="task",
    status="open",
    tags=("teams",),
    priority=1,
    updated="2026-10-01T10:00:00.000000Z",
    created="2026-09-01T10:00:00.000000Z",
    leverage=4,
    assignee="ada",
)


def _rows(page: str) -> list[str]:
    """Each row's markup, from its opening tag to the next row or the list's end."""
    return re.findall(
        r'<div class="kv-row" data-updated=.*?(?=<div class="kv-row"|</section>|$)', page, re.S
    )


def _script(name: str) -> str:
    """One static script's text."""
    return (STATIC / name).read_text(encoding="utf-8")


def test_a_row_shows_status_title_tags_id_type_time_assignee_and_priority(client):
    page = client(DeclaredBacklog(live_value=(TAGGED,))).get("/tickets").text
    (row,) = _rows(page)

    assert 'class="kv-status r-intake" href="/tickets?status=open">open<' in row
    assert (
        ">teams<" in row
        and "kno-r1" in row
        and 'href="/tickets?type=task" title="every task">task<' in row
    )
    assert re.search(r"updated <time class=\"ago\" datetime=\"2026-10-01T10:00:00.000000Z\"", row)
    assert 'href="/tickets?assignee=ada">ada<' in row
    assert 'class="kv-badge p1" href="/tickets?priority=1"' in row and ">P1</a>" in row
    assert "blocked by" not in row and "acceptance" not in row


def test_ordered_by_created_a_row_shows_when_it_was_created(client):
    page = client(DeclaredBacklog(live_value=(TAGGED,))).get("/tickets?order=created").text

    assert 'created <time class="ago" datetime="2026-09-01T10:00:00.000000Z"' in page


def test_a_row_without_a_time_shows_none(client):
    bare = ticket("kno-r3", updated=None, created=None)

    (row,) = _rows(client(DeclaredBacklog(live_value=(bare,))).get("/tickets").text)

    assert "<time" not in row


def test_ordered_by_leverage_each_row_says_how_much_closing_it_frees(client):
    page = client(DeclaredBacklog(live_value=(TAGGED,))).get("/tickets?order=leverage").text

    assert ">frees 4</span>" in page
    assert 'title="closing it frees 4 tickets waiting on it' in page


def test_a_row_that_frees_nothing_says_nothing_about_it_even_ordered_by_leverage(client):
    leaf = ticket("kno-r4", leverage=0)

    (row,) = _rows(client(DeclaredBacklog(live_value=(leaf,))).get("/tickets?order=leverage").text)

    assert "frees" not in row


def test_unordered_by_leverage_the_tickets_list_says_nothing_about_what_a_row_frees(client):
    page = client(DeclaredBacklog(live_value=(TAGGED,))).get("/tickets").text

    assert "frees" not in page


def test_a_row_names_its_document_types_and_a_row_without_documents_names_none(client):
    spec = Document(id="kno-r1-d1", ticket="kno-r1", title="Spec", type="spec")
    owner = ticket("kno-r1", documents=(spec,))
    other = ticket("kno-r2")

    rows = _rows(client(DeclaredBacklog(live_value=(owner, other))).get("/tickets").text)

    assert 'class="kv-doc" href="/ticket/kno-r1#documents" title="spec"' in rows[0]
    assert 'class="kv-docmarks" title="spec">docs' in rows[0]
    assert "kv-docmarks" not in rows[1] and "kv-chip" not in rows[1]


def test_a_rows_first_line_is_its_type_then_its_status_then_its_title_and_nothing_else(client):
    """A reader asks what a ticket is before where it stands, so the type comes first; the two
    flow before the title rather than standing as columns that narrow it."""
    (row,) = _rows(client(DeclaredBacklog(live_value=(TAGGED,))).get("/tickets").text)

    line = row[row.index('<div class="kv-row-title">') : row.index("</div>")]
    assert re.findall(r"<a [^>]*>([^<]*)</a>", line) == ["task", TAGGED.status, TAGGED.title]
    assert line.index('class="kv-type"') < line.index('class="kv-status') < line.index('"title"')


def test_the_type_is_named_once_so_the_muted_line_no_longer_carries_it(client):
    (row,) = _rows(client(DeclaredBacklog(live_value=(TAGGED,))).get("/tickets").text)

    meta = row[row.index('<div class="kv-meta">') :]
    assert row.count('href="/tickets?type=task"') == 1 and ">task<" not in meta


def test_tags_are_a_facets_line_of_key_then_value_each_linking_to_the_whole_tag(client):
    faceted = ticket("kno-r5", tags=("area:pipeline", "init:graph", "teams"))

    (row,) = _rows(client(DeclaredBacklog(live_value=(faceted,))).get("/tickets").text)

    facets = row[row.index('<div class="kv-facets">') : row.index('<div class="kv-meta">')]
    assert (
        '<a href="/tickets?tag=area%3Apipeline"><span class="key">area</span> pipeline</a>'
        in facets
    )
    assert '<a href="/tickets?tag=init%3Agraph"><span class="key">init</span> graph</a>' in facets
    assert '<a href="/tickets?tag=teams">teams</a>' in facets
    assert "kv-chip" not in row


def test_a_tag_with_nothing_on_one_side_of_its_colon_is_shown_whole(client):
    odd = ticket("kno-r6", tags=("area:", ":graph"))

    (row,) = _rows(client(DeclaredBacklog(live_value=(odd,))).get("/tickets").text)

    assert ">area:</a>" in row and ">:graph</a>" in row and 'class="key"' not in row


def test_a_row_without_tags_has_no_facets_line(client):
    bare = ticket("kno-r7", tags=())

    (row,) = _rows(client(DeclaredBacklog(live_value=(bare,))).get("/tickets").text)

    assert "kv-facets" not in row


def test_the_documents_end_the_muted_line_after_every_other_fact(client):
    spec = Document(id="kno-r1-d1", ticket="kno-r1", title="Spec", type="spec")
    owner = ticket("kno-r1", documents=(spec,), assignee="ada")

    (row,) = _rows(client(DeclaredBacklog(live_value=(owner,))).get("/tickets").text)

    meta = row[row.index('<div class="kv-meta">') :]
    assert meta.index(">ada<") < meta.index('class="kv-docmarks"')


def test_clearing_the_tag_pill_leaves_pinned_tags_in_force(client):
    other = ticket("kno-r2", type="task", status="open")
    browser = client(DeclaredBacklog(live_value=(TAGGED, other)))
    browser.cookies.set("knotview_tags", "teams")

    page = browser.get("/tickets").text

    assert len(_rows(page)) == 1 and "kno-r2" not in page
    assert 'class="kv-pinned"' in page


def test_the_filter_form_applies_on_change_and_carries_a_visible_fallback_button(client):
    page = client(DeclaredBacklog()).get("/tickets").text

    assert '<form class="kv-filters" method="get" action="/tickets" data-auto>' in page
    assert '<noscript><button type="submit">Apply</button></noscript>' in page
    assert '<dialog class="kv-dialog" id="more-filters" aria-label="More filters">' in page
    assert 'src="/static/fold.js?v=' in page


def test_more_filters_is_a_button_after_the_pills_counting_what_it_holds(client):
    plain = client(DeclaredBacklog()).get("/tickets").text
    filtered = client(DeclaredBacklog()).get("/tickets?mode=afk&closed=1").text

    assert plain.index('name="order"') < plain.index('data-open="more-filters"')
    assert ">More filters</button>" in plain
    assert 'class="kv-pill set" data-open="more-filters">More filters (2)</button>' in filtered


def test_the_dialog_applies_with_its_own_button_and_cancels_back_to_what_was_applied():
    script = _script("follow.js")

    assert "showModal()" in script and 'closest("dialog")' in script
    assert "form.reset()" in script


def test_an_empty_list_says_so(client):
    page = client(DeclaredBacklog(live_value=())).get("/tickets").text

    assert "Nothing here." in page


def test_follow_js_submits_the_whole_form_on_change_and_never_on_input():
    script = _script("follow.js")

    assert 'querySelectorAll("form[data-auto]")' in script
    assert "new FormData(form)" in script and "location.replace" in script
    assert '"input"' not in script
    assert 'querySelectorAll("[data-updated]")' in script
    assert "knotview:search:" in script


def test_fold_js_matches_stored_ids_against_the_page_and_never_builds_selectors():
    script = _script("fold.js")

    assert 'querySelectorAll("details[data-fold]")' in script
    assert "querySelector(" not in script.replace('querySelector("[data-tabs]")', "")
    assert "innerHTML" not in script
