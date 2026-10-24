"""A ticket's status as a pill coloured by its role, everywhere a ticket is listed or shown."""

import re
from dataclasses import replace
from pathlib import Path

from tests.panel.declared import CHILD, CLOSED, ORPHAN, PARENT, PROJECT, DeclaredBacklog, ticket
from tests.panel.test_compare import FEATURE, _panel, _section, _with

STATIC = Path("src/knotview/panel/static")
# A project with its own words, so a pill coloured by the word rather than the role would fail.
STAGED = replace(
    PROJECT,
    statuses=("todo", "spec", "implement", "done", "dropped"),
    active_status="implement",
    terminal_statuses=("done", "dropped"),
)
STAGED_LIVE = (
    ticket("pro-s1", title="Waiting", status="todo"),
    ticket("pro-s2", title="Designing", status="spec"),
    ticket("pro-s3", title="Building", status="implement"),
)
STAGED_CLOSED = (
    ticket("pro-s4", title="Shipped", status="done"),
    ticket("pro-s5", title="Abandoned", status="dropped"),
)


def _staged(client):
    """A browser over the project with its own words."""
    return client(
        DeclaredBacklog(project_value=STAGED, live_value=STAGED_LIVE, closed_value=STAGED_CLOSED)
    )


def _css() -> str:
    """The panel's own stylesheet."""
    return (STATIC / "panel.css").read_text(encoding="utf-8")


def test_every_row_leads_with_a_pill_linked_to_its_status_and_coloured_by_its_role(client):
    page = _staged(client).get("/tickets?closed=1").text

    for status, role in (
        ("todo", "intake"),
        ("spec", "stage"),
        ("implement", "active"),
        ("done", "closing"),
        ("dropped", "terminal"),
    ):
        assert f'<a class="kv-status r-{role}" href="/tickets?status={status}">{status}</a>' in page
    assert "kv-dot s-" not in page


def test_the_stylesheet_colours_five_roles_and_not_one_word():
    css = _css()

    for role in ("intake", "active", "stage", "closing", "terminal"):
        assert f".kv-status.r-{role} {{" in css
    assert ".kv-dot.s-todo" not in css and ".kv-status.s-" not in css


def test_a_terminal_ticket_s_row_recedes_to_a_muted_title():
    assert re.search(
        r"\.kv-row:has\([^{]*\.kv-row-title > \.kv-status\.r-closing,"
        r"[^{]*\.kv-row-title > \.kv-status\.r-terminal,[^{]*\)\s*\.title \{\s*"
        r"color: var\(--fgColor-muted\);",
        _css(),
    )


def test_the_ticket_page_leads_with_a_large_pill_and_pills_its_related_tickets(client):
    page = client(DeclaredBacklog()).get(f"/ticket/{CHILD.id}").text

    assert (
        '<a class="kv-status r-active large" href="/tickets?status=in_progress">in_progress</a>'
        in page
    )
    # Related tickets are drawn in the shared row, whose pill opens the list of that status.
    for related, pill in (
        (ORPHAN, '<a class="kv-status r-intake" href="/tickets?status=open">open</a>'),
        (CLOSED, '<a class="kv-status r-closing" href="/tickets?status=closed">closed</a>'),
    ):
        row = page[: page.index(f'href="/ticket/{related.id}"')]
        assert row.rindex(pill) > row.rindex('<div class="kv-row"')
    assert "kv-dot s-" not in page


def test_the_depends_on_tree_pills_each_node(client):
    page = client(DeclaredBacklog()).get(f"/ticket/{CHILD.id}").text
    tree = page[page.index("depends on, all the way down") :]

    assert f'<a class="kv-status r-closing" href="/ticket/{CLOSED.id}">closed</a>' in tree


def test_the_tree_pills_its_branches_and_leaves(client):
    page = client(DeclaredBacklog()).get("/tree").text

    assert '<a class="kv-status r-intake" href="/tickets?status=open">open</a>' in page
    assert "kv-dot s-" not in page


def test_the_recent_cards_give_the_title_the_width_and_type_and_status_under_it(client):
    """As columns before the title, the type and pill left a narrow card's title too thin."""
    page = client(DeclaredBacklog()).get("/").text
    changed = page[page.index("recently changed") : page.index("recently closed")]
    closed = page[page.index("recently closed") :]

    assert re.search(
        r'<div class="kv-row">\s*<div class="kv-row-main">\s*<a class="title"[^>]*>[^<]*</a>'
        r'\s*<div class="kv-meta"><a class="kv-type"[^>]*>task</a><a class="kv-status r-active" '
        r'href="/tickets\?status=in_progress">in_progress</a><span class="kv-mono">',
        changed,
    )
    assert '<a class="kv-status r-closing" href="/tickets?status=closed">closed</a>' in closed


def test_the_overview_s_headline_dots_take_their_status_s_role_colour(client):
    page = _staged(client).get("/").text
    headline = page[page.index('<div class="kv-stats">') :].split("</div>", 1)[0]

    for status, role in (("Todo", "intake"), ("Spec", "stage"), ("Implement", "active")):
        assert f'<span class="kv-dot r-{role}">{status}</span><strong>' in headline
    assert "kv-dot s-" not in page


def test_the_status_charts_colour_each_bar_and_dot_by_role(client):
    page = _staged(client).get("/").text

    for status, role in (("todo", "intake"), ("done", "closing"), ("dropped", "terminal")):
        assert re.search(
            rf'<span class="kv-dot r-{role}">{status}</span><span class="kv-track">'
            rf'<span class="kv-fill r-{role}"',
            page,
        )
    assert "kv-fill s-" not in page


def test_the_stylesheet_keeps_no_colour_for_a_status_word():
    css = _css()

    for role in ("intake", "active", "stage", "closing", "terminal"):
        assert f".kv-dot.r-{role}::before,\n.kv-fill.r-{role} {{" in css
    assert not re.search(r"\.(kv-dot|kv-fill)\.s-", css)


def test_each_parent_on_the_overview_leads_with_its_type_then_its_status_pill(client):
    parent = ticket("pro-s6", title="The stage parent", status="spec")
    kid = ticket("pro-s7", title="A kid", parent="pro-s6", status="todo")
    browser = client(DeclaredBacklog(project_value=STAGED, live_value=(parent, kid)))

    page = browser.get("/").text

    assert re.search(
        r'<a class="kv-badge p2"[^>]*>P2</a>\s*<div class="kv-row-main">\s*'
        r'<div class="kv-row-title compact"><a class="kv-type"[^>]*>task</a>'
        r'<a class="kv-status r-stage" href="/tickets\?status=spec">spec</a><a class="title"',
        page,
    )


def test_a_compared_status_reads_as_two_pills_from_here_to_there(client):
    browser, _ = _panel(client)

    parted = _section(browser.get(_with(FEATURE)).text, "closed on one side, live on the other")

    assert re.search(
        r'<span class="kv-status r-active">in_progress</span></span>\s*'
        r'<span class="kv-muted" aria-label="[^"]*">→</span>\s*'
        r'<span title="[^"]*"><span class="kv-status r-closing">closed</span>',
        parted,
    )


def test_a_compared_field_other_than_status_stays_plain_text(client):
    browser, _ = _panel(client)

    changed = _section(browser.get(_with(FEATURE)).text, ">changed <span")

    assert PARENT.title in changed and '<span title="in main · knotview">1</span>' in changed


def test_the_ticket_page_header_leads_with_its_type_then_its_status(client):
    page = client(DeclaredBacklog()).get(f"/ticket/{CHILD.id}").text
    summary = page[page.index('<p class="kv-summary">') :].split("</p>", 1)[0]

    assert summary.index('class="kv-type large"') < summary.index(
        'class="kv-status r-active large"'
    )
    assert 'title="every task">task</a>' in summary and 'kv-muted"><a' not in summary
