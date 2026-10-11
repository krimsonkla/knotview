"""What each captured view must show, checked on its HTML before a screenshot is kept.

A screenshot of a view with nothing in it is worse than none: the README would show an empty
queue as if that were the panel. The capture script asks this for every view and stops on a
refusal, naming the view.
"""

EXPECTED = {
    "overview": 'class="kv-stat"',
    "tickets": 'class="kv-row" data-updated',
    "tree": 'class="kv-branch"',
    "ready": 'class="kv-row" data-updated',
    "blocked": 'class="kv-row" data-updated',
    "ticket": 'id="documents"',
    "document": 'aria-label="On this page"',
}


def missing(view: str, html: str) -> None:
    """Refuse a view whose page lacks the content it exists to show."""
    assert EXPECTED[view] in html, f"{view}: the page shows none of {EXPECTED[view]!r}"
