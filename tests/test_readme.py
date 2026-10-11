"""The README shows every view at once, and every image it names exists within budget."""

import re
from pathlib import Path

README = Path("README.md").read_text(encoding="utf-8")
IMAGES = re.findall(r"!\[[^\]]*\]\(([^)\s]+)\)", README) + re.findall(
    r'<img[^>]+src="([^"]+)"', README
)


def test_the_readme_hides_nothing_behind_details():
    assert "<details" not in README


def test_every_image_the_readme_names_exists():
    assert IMAGES
    assert [one for one in IMAGES if not Path(one).is_file()] == []


def test_images_keep_to_the_budget_and_no_stale_screenshot_remains():
    for one in IMAGES:
        limit = 1_500_000 if Path(one).suffix in (".webp", ".gif") else 250_000
        assert Path(one).stat().st_size <= limit, one
    named = {Path(one).name for one in IMAGES}
    assert {one.name for one in Path("docs/screenshots").iterdir()} <= named


def test_the_readme_says_which_theme_and_that_the_panel_follows_the_system():
    assert "dark theme" in README and "follows your system" in README
    assert re.search(r"!\[[^\]]+\]\(docs/screenshots/tour\.(webp|gif)\)", README)
