"""Ticket text rendered as a page reads it, and never trusted."""

from knotview.panel.prose import rendered, split
from tests.panel.declared import DeclaredBacklog, ticket


def test_lists_code_and_emphasis_become_elements():
    html = rendered("- one\n- two\n\nSome `code` and **bold**.")

    assert "<li>one</li>" in html
    assert "<code>code</code>" in html and "<strong>bold</strong>" in html


def test_raw_html_in_a_ticket_is_text_not_markup():
    html = rendered("<script>alert(1)</script> and <b>b</b>")

    assert "<script>" not in html and "&lt;script&gt;" in html and "&lt;b&gt;" in html


def test_a_tickets_own_headings_sit_below_the_sections():
    html = rendered("# top\n\n## second\n\n##### deep")

    assert "<h3>top</h3>" in html and "<h4>second</h4>" in html and "<h6>deep</h6>" in html


def test_the_ticket_page_renders_sections_and_notes_as_markdown(client):
    held = ticket(
        "pro-01m2mmmmmmmm",
        title="Marked down",
        sections={
            "description": "A *list*:\n\n- first\n- second",
            "notes": "**2026-09-13T00:00:00Z**\n\nSaid `so`.",
        },
    )
    page = client(DeclaredBacklog(live_value=(held,))).get("/ticket/pro-01m2mmmmmmmm").text

    assert "<em>list</em>" in page and "<li>first</li>" in page and "<code>so</code>" in page


def test_a_markdown_table_renders_as_a_table_and_html_in_it_stays_text():
    html = rendered("| a | b |\n|---|---|\n| <script>x</script> | [y](javascript:z) |\n")

    assert "<table>" in html and "<th>a</th>" in html
    assert "&lt;script&gt;" in html and "<script>" not in html
    assert 'href="javascript' not in html


def test_split_keeps_the_first_two_blocks_and_renders_the_rest_apart():
    head, rest = split("one\n\ntwo\n\nthree\n\n- four\n")

    assert head.count("<p>") == 2 and "three" not in head
    assert "<p>three</p>" in rest and "<li>four</li>" in rest


def test_split_of_a_short_text_leaves_nothing_to_fold():
    head, rest = split("only one paragraph")

    assert "only one paragraph" in head and rest == ""


def test_split_counts_a_whole_table_as_one_block():
    head, rest = split("| a |\n|---|\n| b |\n\nafter\n\nlast\n")

    assert "<table>" in head and "</table>" in head and "after" in head
    assert "last" in rest
