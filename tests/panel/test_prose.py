"""Ticket text rendered as a page reads it, and never trusted."""

from knotview.panel.prose import rendered
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
