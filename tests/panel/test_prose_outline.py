"""A document's body with anchored headings and the outline that links to them."""

from knotview.panel import prose
from knotview.panel.prose import Outline, outlined


def test_headings_are_demoted_once_anchored_and_the_top_two_levels_outlined():
    html, outline = outlined("# Plan\n\n## Plan\n\n### Deep\n")

    assert '<h2 id="doc-plan">Plan</h2>' in html
    assert '<h3 id="doc-plan-2">Plan</h3>' in html
    assert '<h4 id="doc-deep">Deep</h4>' in html
    assert outline == (
        Outline(level=2, text="Plan", anchor="doc-plan"),
        Outline(level=3, text="Plan", anchor="doc-plan-2"),
    )


def test_outline_text_is_the_headings_words_without_their_markup():
    _, outline = outlined("# **Rollout** `x` now\n")

    assert outline == (Outline(level=2, text="Rollout x now", anchor="doc-rollout-x-now"),)


def test_a_heading_carrying_markup_is_escaped_in_its_text_and_its_id():
    html, _ = outlined('# a"><script>x</script>\n')

    assert "<script>" not in html
    assert 'id="doc-a-script-x-script"' in html


def test_raw_html_in_the_body_stays_text():
    html, _ = outlined("<b>bold</b>\n")

    assert "&lt;b&gt;bold&lt;/b&gt;" in html


def test_a_heading_of_only_punctuation_is_still_anchored():
    html, outline = outlined("# !!!\n")

    assert 'id="doc-section"' in html and outline[0].anchor == "doc-section"


def test_an_anchor_is_escaped_by_the_renderer_whatever_the_slug_lets_through(monkeypatch):
    monkeypatch.setattr(prose, "_slug", lambda words: '"><img src=x>')

    html, _ = outlined("# anything\n")

    assert "<img" not in html and 'id="doc-&quot;&gt;&lt;img src=x&gt;"' in html


def test_the_outline_starts_at_the_documents_own_top_level():
    _, outline = outlined("## One\n\n### Two\n\n#### Three\n\n## Four\n")

    assert [(one.level, one.text) for one in outline] == [(3, "One"), (4, "Two"), (3, "Four")]


def test_a_heading_with_no_words_is_anchored_but_not_outlined():
    html, outline = outlined("## ![](x.png)\n\n## Real\n")

    assert 'id="doc-section"' in html
    assert [one.text for one in outline] == ["Real"]
