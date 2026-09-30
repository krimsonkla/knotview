"""The first page: the backlog counted the ways a reader asks about it."""

import re
from datetime import UTC, datetime
from pathlib import Path

from knotview.panel.app import _ago
from knotview.reading.knot_command import _issue
from knotview.values.attention import Attention
from knotview.values.criterion import Criterion
from knotview.values.issue import Issue
from tests.panel.declared import CHILD, PARENT, DeclaredBacklog, ticket
from tests.reading.envelopes import envelope


def test_every_declared_type_is_counted_even_at_zero_with_a_link_to_its_filter(client):
    page = client(DeclaredBacklog()).get("/").text

    assert '<a href="/tickets?type=feature"' in page
    assert "epic" in page and "chore" in page


def test_statuses_priorities_and_queues_are_counted(client):
    page = client(DeclaredBacklog()).get("/").text

    assert '<a href="/tickets?status=in_progress"' in page
    assert '<a href="/tickets?priority=3"' in page
    assert '<a href="/queue/ready">ready</a>' in page
    assert '<a href="/tickets?assignee=nobody">unassigned</a>' in page
    assert 'href="/tickets?status=closed&amp;closed=1"' in page and ">closed</a" in page
    assert "archive_count" not in page


def test_the_live_total_is_the_sum_over_statuses(client):
    page = client(DeclaredBacklog()).get("/").text

    assert re.search(r'<a href="/tickets">live</a\s*><span class="num">3</span>', page)


def test_parents_are_whatever_something_is_filed_under_and_closed_work_is_listed(client):
    page = client(DeclaredBacklog()).get("/").text

    assert "The parent" in page
    assert "The closed one" in page


def test_recently_closed_is_capped(client):
    many = tuple(
        ticket(f"pro-01m2{i:08d}", status="closed", title=f"Closed {i}") for i in range(10)
    )
    page = client(DeclaredBacklog(closed_value=many)).get("/").text

    assert "Closed 7" in page and "Closed 8" not in page


def test_a_clean_project_shows_no_integrity_section(client):
    assert "integrity" not in client(DeclaredBacklog()).get("/").text


def test_integrity_issues_are_listed_as_knot_reported_them_at_200(client):
    """AC 3: the line comes from the recorded check through the real reader."""
    issues = tuple(
        _issue(one, Path("/probe")) for one in envelope("check-issues")["data"]["issues"]
    )

    response = client(DeclaredBacklog(integrity_value=issues)).get("/")

    assert response.status_code == 200
    assert '<a href="/ticket/pro-01m2bbbbbbbb">pro-01m2bbbbbbbb</a>' in response.text
    assert "unknown_id: unknown id" in response.text
    assert "/document/" not in response.text


def test_a_document_issue_links_its_document_and_shows_its_path_from_the_project(client):
    memo = Issue.found(
        "invalid_doc_type: has type memo",
        "/probe/.tickets/docs/pro-01m2aaaaaaaa/pro-01m2aaaaaaaa-d5memo--memo.md",
        Path("/probe"),
        ("pro-01m2aaaaaaaa-d5memo",),
    )

    text = client(DeclaredBacklog(integrity_value=(memo,))).get("/").text

    assert '<a href="/document/pro-01m2aaaaaaaa-d5memo">pro-01m2aaaaaaaa-d5memo</a>' in text
    assert text.count(">pro-01m2aaaaaaaa-d5memo<") == 1
    assert "d5memo invalid_doc_type" not in text  # named once, by its link
    assert (
        f'title="{memo.path}">.tickets/docs/pro-01m2aaaaaaaa/pro-01m2aaaaaaaa-d5memo--memo.md<'
        in text
    )


def test_an_issue_with_no_documents_and_no_path_is_its_text_alone(client):
    plain = (Issue(text="pro-01m2aaaaaaaa legacy_documents_section: a heading"),)

    text = client(DeclaredBacklog(integrity_value=plain)).get("/").text
    card = text[text.index("<h2>integrity</h2>") : text.index("</section>")]

    assert "legacy_documents_section" in card
    assert "/document/" not in card and 'class="id"' not in card


def test_a_path_outside_the_project_is_shown_whole(client):
    orphan = Issue.found("an orphan", "/elsewhere/d.md", Path("/probe"), ("pro-1-d1x",))

    text = client(DeclaredBacklog(integrity_value=(orphan,))).get("/").text

    assert 'title="/elsewhere/d.md">/elsewhere/d.md<' in text


def test_ready_to_close_and_stale_are_shown_when_the_primer_reports_them(client):
    old = ticket("pro-01m2oooooooo", title="Started and stopped", status="in_progress")
    report = Attention(in_progress=(CHILD, old), ready_to_close=(CHILD,), stale=(old,))
    page = client(DeclaredBacklog(attention_value=report)).get("/").text

    assert "ready to close" in page and "close these before picking up new work" in page
    assert "stale" in page and "Started and stopped" in page


def test_neither_section_appears_when_the_primer_reports_nothing(client):
    page = client(DeclaredBacklog()).get("/").text

    assert "ready to close" not in page and "Started and stopped" not in page


def test_recently_changed_lists_live_tickets_newest_first_with_a_relative_time(client):
    page = client(DeclaredBacklog()).get("/").text

    section = page[page.index("recently changed") : page.index("recently closed")]
    assert section.index("The child") < section.index("The parent") < section.index("The orphan")
    assert (
        '<time class="ago" datetime="2026-09-04T10:00:00.000000Z" '
        'title="2026-09-04T10:00:00.000000Z">' in section
    )
    assert "d ago</time>" in section


def test_a_recently_changed_ticket_without_an_updated_instant_shows_a_dash(client):
    bare = ticket("pro-01m2eeeeeeee", title="Never saved", updated=None)
    page = client(DeclaredBacklog(live_value=(bare,))).get("/").text

    section = page[page.index("recently changed") : page.index("recently closed")]
    assert "Never saved" in section and '<span class="muted">—</span>' in section
    assert 'class="ago"' not in section


def test_the_recently_closed_cells_are_stamps(client):
    page = client(DeclaredBacklog()).get("/").text

    closed = page[page.index("recently closed") :]
    assert '<time class="stamp" datetime="2026-09-02T10:00:00.000000Z" title=' in closed


def test_an_instant_reads_as_a_distance_from_now():
    now = datetime(2026, 9, 14, 12, 0, tzinfo=UTC)

    assert _ago("2026-09-14T11:59:40Z", now) == "just now"
    assert _ago("2026-09-14T11:15:00Z", now) == "45 min ago"
    assert _ago("2026-09-14T03:00:00Z", now) == "9 h ago"
    assert _ago("2026-09-01T10:00:00.000000Z", now) == "13 d ago"
    assert _ago(None) == "—" and _ago("not an instant") == "not an instant"
    assert (
        _ago("2026-09-14T11:59:59Z").endswith("ago") or _ago("2026-09-14T11:59:59Z") == "just now"
    )


def test_progress_lists_parents_with_criteria_nearest_to_done_first(client):
    far = ticket(
        "pro-01m2ffffffff",
        title="Far parent",
        acceptance=tuple(Criterion(title=f"c{i}", done=False) for i in range(4)),
    )
    kid = ticket("pro-01m2kkkkkkkk", parent="pro-01m2ffffffff")
    page = client(DeclaredBacklog(live_value=(far, kid, PARENT, CHILD))).get("/").text

    section = page[page.index("<h2>progress</h2>") : page.index("<h2>parents</h2>")]
    assert section.index("The parent") < section.index("Far parent")
    assert '<progress value="1" max="2">' in section and "1/2 criteria" in section
    assert "1 live beneath" in section


def test_a_parent_without_criteria_is_not_in_progress(client):
    bare = ticket("pro-01m2pppppppp", title="Bare parent")
    kid = ticket("pro-01m2qqqqqqqq", parent="pro-01m2pppppppp")
    page = client(DeclaredBacklog(live_value=(bare, kid))).get("/").text

    assert "<h2>progress</h2>" not in page


def test_overview_cards_link_only_their_rows_filter_whatever_the_url_holds(client):
    """The overview ignores its query string (kno-01m3qneqctfh): a carried filter made a count
    disagree with the list its link opened."""
    page = client(DeclaredBacklog()).get("/?type=task").text

    assert 'href="/tickets?status=in_progress"' in page
    assert 'href="/tickets?priority=3"' in page and "type=task&amp;" not in page


def test_the_terminal_count_narrows_with_the_chosen_tags(client):
    closed_tagged = ticket("pro-01m2tttttttt", status="closed", tags=("auth",))
    closed_plain = ticket("pro-01m2uuuuuuuu", status="closed")
    browser = client(DeclaredBacklog(closed_value=(closed_tagged, closed_plain)))

    before = browser.get("/").text
    browser.get("/tags?add=auth&back=/")
    after = browser.get("/").text

    def closed_count(page: str) -> str:
        start = page.index(">closed</a")
        return page[start : start + 80].split('<span class="num">')[1].split("<")[0]

    assert closed_count(before) == "2" and closed_count(after) == "1"


def test_a_cycle_reads_as_its_tickets_linked_once_then_knots_own_sentence(client):
    """The whole item, since links, text and path compose into one line. The ids recur inside
    knot's message, which is knot's wording, not a second drawing of them."""
    cycle = _issue(
        {
            "severity": "error",
            "code": "dep_cycle",
            "ids": ["pro-a", "pro-b", "pro-c", "pro-d", "pro-a"],
            "message": "dep cycle: pro-a -> pro-b -> pro-c -> pro-d -> pro-a",
        },
        Path("/probe"),
    )

    text = client(DeclaredBacklog(integrity_value=(cycle,))).get("/").text
    item = re.sub(r"\s+", " ", text[text.index("<h2>integrity</h2>") : text.index("</ul>")])
    item = item[item.index("<li>") : item.index("</li>") + 5]

    assert item == (
        '<li> <a href="/ticket/pro-a">pro-a</a> <a href="/ticket/pro-b">pro-b</a> '
        '<a href="/ticket/pro-c">pro-c</a> <a href="/ticket/pro-d">pro-d</a> '
        "dep_cycle: dep cycle: pro-a -&gt; pro-b -&gt; pro-c -&gt; pro-d -&gt; pro-a </li>"
    )


def test_an_issue_with_no_ids_still_shows_the_file_it_is_about(client):
    broken = _issue(
        {
            "severity": "error",
            "code": "frontmatter_parse_error",
            "ids": [],
            "path": "/probe/.tickets/pro-x--broken.md",
            "message": "frontmatter parse error at /probe/.tickets/pro-x--broken.md",
        },
        Path("/probe"),
    )

    text = client(DeclaredBacklog(integrity_value=(broken,))).get("/").text
    card = text[text.index("<h2>integrity</h2>") : text.index("</section>")]

    assert ">.tickets/pro-x--broken.md</span>" in card and "/ticket/" not in card
