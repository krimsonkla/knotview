"""The first page: the backlog counted the ways a reader asks about it."""

import re
from datetime import UTC, datetime
from pathlib import Path

from knotview.panel.app import _ago
from knotview.panel.overview import _named, _plural, _start_here
from knotview.reading.knot_command import _issue
from knotview.values.attention import Attention
from knotview.values.criterion import Criterion
from knotview.values.issue import Issue
from tests.panel.declared import CHILD, DeclaredBacklog, ticket
from tests.reading.envelopes import envelope


def test_every_declared_type_is_counted_even_at_zero_with_a_link_to_its_filter(client):
    page = client(DeclaredBacklog()).get("/").text

    assert '<a class="kv-bar" href="/tickets?type=feature"' in page
    assert "epic" in page and "chore" in page


def test_statuses_priorities_and_queues_are_counted(client):
    page = client(DeclaredBacklog()).get("/").text

    assert 'href="/tickets?status=in_progress" data-card="by status"' in page
    assert 'href="/tickets?priority=3" data-card="by priority"' in page
    assert 'href="/queue/ready" data-card="queues"><span>ready</span>' in page
    assert 'href="/tickets?assignee=nobody" data-card="queues"><span>unassigned</span>' in page
    closed = 'href="/tickets?status=closed&amp;closed=1" data-card="by status">'
    assert closed + '<span class="kv-dot r-closing">closed<' in page
    assert "archive_count" not in page


def test_the_live_total_is_the_sum_over_statuses(client):
    page = client(DeclaredBacklog()).get("/").text

    live = r'href="/tickets" data-card="queues"><span>live</span>'
    assert re.search(live + r'.*?<span class="kv-num">3</span>', page)


def test_parents_are_whatever_something_is_filed_under_and_closed_work_is_listed(client):
    page = client(DeclaredBacklog()).get("/").text

    assert "The parent" in page
    assert "The closed one" in page


def test_recently_closed_is_capped(client):
    many = tuple(
        ticket(f"pro-01m2{i:08d}", status="closed", title=f"Closed {i}") for i in range(10)
    )
    page = client(DeclaredBacklog(closed_value=many)).get("/").text

    assert "Closed 4" in page and "Closed 5" not in page


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


def test_a_recently_changed_ticket_without_an_updated_instant_shows_no_time(client):
    bare = ticket("pro-01m2eeeeeeee", title="Never saved", updated=None)
    page = client(DeclaredBacklog(live_value=(bare,))).get("/").text

    section = page[page.index("recently changed") : page.index("recently closed")]
    assert "Never saved" in section and 'class="ago"' not in section


def test_the_recently_closed_rows_carry_their_instant(client):
    page = client(DeclaredBacklog()).get("/").text

    closed = page[page.index("recently closed") :]
    assert '<time class="ago" datetime="2026-09-02T10:00:00.000000Z" title=' in closed


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


def test_a_parent_with_criteria_shows_them_in_its_own_row_and_no_second_card(client):
    """Parents with criteria once drew a second card listing the same parents again."""
    far = ticket(
        "pro-01m2ffffffff",
        title="Far parent",
        acceptance=(
            Criterion(title="a", done=True),
            *(Criterion(title=f"c{i}", done=False) for i in range(3)),
        ),
    )
    kid = ticket("pro-01m2kkkkkkkk", parent="pro-01m2ffffffff")
    page = client(DeclaredBacklog(live_value=(far, kid))).get("/").text

    assert "<h2>progress</h2>" not in page
    main = page[: page.index('<div class="kv-narrow">')]
    assert main.count('href="/ticket/pro-01m2ffffffff"') == 1
    row = page[page.index("Far parent") : page.index("0 of 1 done")]
    assert "criteria 1/4" in row


def test_a_parent_without_criteria_shows_no_criteria_count(client):
    bare = ticket("pro-01m2pppppppp", title="Bare parent")
    kid = ticket("pro-01m2qqqqqqqq", parent="pro-01m2pppppppp")
    page = client(DeclaredBacklog(live_value=(bare, kid))).get("/").text

    assert "<h2>progress</h2>" not in page and "criteria" not in page[page.index("Bare parent") :]


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
        start = page.index('closed=1" data-card="by status"><span class="kv-dot r-closing">closed')
        return page[start : start + 300].split('<span class="kv-num">')[1].split("<")[0]

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


EPIC = ticket("pro-01m2e1111111", title="The epic", type="epic")
KIDS = (
    ticket("pro-01m2k1111111", title="Kid one", parent="pro-01m2e1111111"),
    ticket("pro-01m2k2222222", title="Kid two", status="closed", parent="pro-01m2e1111111"),
)


def test_the_overview_shows_stat_cards_bars_and_epic_progress(client):
    backlog = DeclaredBacklog(live_value=(EPIC, KIDS[0]), closed_value=(KIDS[1],))

    page = client(backlog).get("/").text

    for label in ("Open", "In progress", "Ready", "Blocked"):
        assert f">{label}</span><strong>" in page
    assert page.count('class="kv-bar"') >= 3
    assert "1 of 2 done" in page


def test_an_epic_with_no_closed_children_shows_none_done(client):
    page = client(DeclaredBacklog(live_value=(EPIC, KIDS[0]), closed_value=())).get("/").text

    assert "0 of 1 done" in page


def test_priority_and_type_charts_show_and_the_rest_wait_behind_the_charts_menu(client):
    page = client(DeclaredBacklog()).get("/").text

    assert '<section class="kv-card" data-chart="by priority">' in page
    assert '<section class="kv-card" data-chart="by type">' in page
    for hidden in ("by status", "closed", "queues"):
        assert f'<section class="kv-card" data-chart="{hidden}" hidden>' in page
        assert f'data-chart-toggle="{hidden}" />' in page
    assert 'data-chart-toggle="by type" checked' in page


def test_the_parents_card_is_named_by_the_types_its_parents_have(client):
    epics = client(DeclaredBacklog()).get("/").text
    task = ticket("pro-01m2t1111111", title="Task parent")
    under = ticket("pro-01m2t2222222", parent="pro-01m2t1111111")
    mixed = client(DeclaredBacklog(live_value=(task, under, *DeclaredBacklog().live_value)))

    assert "<h2>epics</h2>" in epics and "<h2>parents</h2>" not in epics
    assert "<h2>tasks and epics</h2>" in mixed.get("/").text


def test_type_names_are_made_plural_the_way_english_does():
    assert [_plural(one) for one in ("bug", "story", "fix", "patch", "day")] == [
        "bugs",
        "stories",
        "fixes",
        "patches",
        "days",
    ]


def test_parents_of_no_declared_type_fall_back_to_the_plain_word():
    assert _named((ticket("x", type="nonsense"),), ("bug", "epic")) == "parents"


def test_the_overview_marks_nothing_since_the_last_look(client):
    stale = Attention(in_progress=(), ready_to_close=(), stale=(CHILD,))

    page = client(DeclaredBacklog(attention_value=stale)).get("/").text

    assert "data-updated=" not in page and "The child" in page


def test_a_gear_in_the_overview_header_opens_the_charts_dialog(client):
    overview = client(DeclaredBacklog()).get("/").text
    tickets = client(DeclaredBacklog()).get("/tickets").text

    header = overview.split("</header>")[0]
    assert 'data-open-dialog="charts-dialog" aria-label="Overview settings"' in header
    assert '<dialog class="kv-dialog" id="charts-dialog" aria-label="Charts">' in overview
    assert '<form class="kv-dialog-foot" method="dialog">' in overview
    assert "data-open-dialog" not in tickets.split("</header>")[0]
    assert '<circle cx="8" cy="8" r="5" stroke-width="3" stroke-dasharray' in header


def test_with_nothing_filed_under_anything_the_card_lists_what_is_ready(client):
    flat = (
        ticket("pro-01m2r1111111", title="Ready one", priority=1),
        ticket("pro-01m2r2222222", title="Ready zero", priority=0),
    )
    backlog = DeclaredBacklog(live_value=flat, ready_value=flat, closed_value=())

    page = client(backlog).get("/").text
    card = page[page.index('<section class="kv-card kv-wide">') :]
    card = card[: card.index("</section>")]

    assert "<h2>ready</h2>" in card
    assert card.index("Ready zero") < card.index("Ready one")
    assert "frees" not in card

    assert 'href="/queue/ready">See all 2 ready</a>' in card


def test_with_nothing_ready_either_the_card_lists_the_open_tickets(client):
    flat = (ticket("pro-01m2o1111111", title="Waiting", priority=2),)
    backlog = DeclaredBacklog(live_value=flat, ready_value=(), closed_value=())

    card = client(backlog).get("/").text.split('<section class="kv-card kv-wide">')[1]

    assert "<h2>open tickets</h2>" in card and "Waiting" in card
    assert 'href="/tickets">See all 1</a>' in card


def test_the_ready_card_leads_with_what_frees_most_and_says_how_much(client):
    flat = (
        ticket("pro-01m2r1111111", title="Urgent leaf", priority=0, leverage=0),
        ticket("pro-01m2r2222222", title="Frees two", priority=3, leverage=2),
    )
    backlog = DeclaredBacklog(live_value=flat, ready_value=flat, closed_value=())

    card = client(backlog).get("/").text.split('<section class="kv-card kv-wide">')[1]
    card = card[: card.index("</section>")]

    assert card.index("Frees two") < card.index("Urgent leaf")
    assert card.count(">frees 2</span>") == 1 and "start here" not in card


def test_with_parents_the_overview_points_at_the_ready_tickets_that_free_most(client):
    top = ticket("pro-01m2t1111111", title="Frees three", leverage=3, priority=2)
    tie = ticket("pro-01m2t2222222", title="Also frees three", leverage=3, priority=1)
    less = ticket("pro-01m2t3333333", title="Frees one", leverage=1)

    page = client(DeclaredBacklog(ready_value=(less, top, tie))).get("/").text
    pointer = page[page.index('<h2 class="kv-wave">start here</h2>') :]
    pointer = pointer[: pointer.index("</section>")]

    assert "closing any of these frees the most tickets" in pointer
    assert 'href="/queue/ready">The ready queue</a>' in pointer
    assert pointer.index("Also frees three") < pointer.index("Frees three")
    assert pointer.count(">frees 3</span>") == 2 and "Frees one" not in pointer


def test_start_here_waits_behind_the_gear_until_the_reader_asks_for_it(client):
    top = ticket("pro-01m2t1111111", title="Frees three", leverage=3)

    page = client(DeclaredBacklog(ready_value=(top,))).get("/").text

    assert '<section data-chart="start here" hidden>' in page
    assert 'data-chart-toggle="start here" />' in page


def test_one_ticket_that_frees_most_is_pointed_at_as_it(client):
    top = ticket("pro-01m2t1111111", title="Frees three", leverage=3)

    page = client(DeclaredBacklog(ready_value=(top, CHILD))).get("/").text

    assert "start here" in page and "closing it frees the most tickets" in page


def test_no_pointer_shows_when_no_ready_ticket_frees_anything(client):
    page = client(DeclaredBacklog()).get("/").text

    assert "start here" not in page


def test_the_pointer_holds_only_the_ties_at_the_top_and_at_most_three():
    many = (*(ticket(f"pro-{at}", leverage=4) for at in range(5)), ticket("x", leverage=9))

    assert [one.id for one in _start_here(many)] == ["x"]
    assert [one.id for one in _start_here(many[:5])] == ["pro-0", "pro-1", "pro-2"]
    assert not _start_here((ticket("y", leverage=0), ticket("z"))) and not _start_here(())


def test_recent_rows_name_each_ticket_s_type_and_its_assignee_where_it_has_one(client):
    page = client(DeclaredBacklog()).get("/").text

    changed = page[page.index("recently changed") : page.index("recently closed")]
    closed = page[page.index("recently closed") :]
    orphan = changed[changed.index("The orphan") :].split("</div>", 1)[0]
    assert 'class="kv-type" href="/tickets?type=bug"' in changed
    assert '<a href="/tickets?assignee=someone">someone</a>' in orphan
    assert 'class="kv-type" href="/tickets?type=chore"' in closed and "assignee=" not in closed
