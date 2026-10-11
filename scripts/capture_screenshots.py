"""Regenerate the README's screenshots and its slideshow from a demo backlog built for the purpose.

The live `.tickets/` changes with every commit and is mostly closed, so it makes a poor picture.
This builds a small backlog with knot in a temporary directory instead: epics with children, a
blocked chain, ready work, something in progress, and documents with a table in them. It moves
every ticket's times back over the last month so relative times read naturally, serves it with
the real `knotview` on loopback, checks each view shows what it is for, takes each screenshot
with headless Chrome in a fresh profile and the dark theme, and builds the inline images and an
animated WebP slideshow from the same captures. Nothing under the repository's `.tickets/` is
read or written.

    uv run python scripts/capture_screenshots.py

Set KNOTVIEW_CHROME to the Chrome binary when it is not at the macOS default.
"""

import http.client
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path

from PIL import Image

from scripts.capture_check import missing

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "docs/screenshots"
PORT = 7790
CHROME = os.environ.get(
    "KNOTVIEW_CHROME", "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
)
WIDTH, HEIGHT = 1440, 1000
INLINE_LIMIT = 250_000
TOUR_LIMIT = 1_500_000

SPEC = """## Problem

Checkout loses one buyer in five between the cart and the payment step.

## Goal

Cut the steps from four to two, and keep every saved card one tap away.

| Step | Today | After |
|---|---|---|
| Address | typed | autocompleted |
| Card | retyped | saved card first |
| Review | separate page | sticky summary |

## Acceptance

- A returning buyer pays in two taps.
- A failed card shows why, inline.
"""

PLAN = """## Tasks

1. Saved cards first, behind the payment provider's vault.
2. Address autocomplete with a manual fallback.
3. A sticky order summary on narrow screens.

## Rollout

Behind a flag, 10 percent of buyers first, then everyone after a week.
"""


def knot(demo: Path, *args: str, stdin: str | None = None) -> dict:
    """One knot command in the demo backlog, its JSON envelope's data."""
    answer = subprocess.run(
        ["knot", *args, "--json"],
        cwd=demo,
        input=stdin,
        capture_output=True,
        text=True,
        check=True,
    )
    return json.loads(answer.stdout)["data"]


def created(demo: Path, title: str, *flags: str) -> str:
    """A new demo ticket's id."""
    return knot(demo, "create", title, *flags)["id"]


def build(demo: Path) -> dict[str, str]:
    """The demo backlog, returning the id of the ticket whose page and document are captured."""
    subprocess.run(["knot", "init", "--prefix", "acme"], cwd=demo, check=True, capture_output=True)
    config = (demo / ".knot.edn").read_text(encoding="utf-8")
    config = config.replace("{\n", '{\n :project-name "acme-shop"\n :default-assignee nil\n', 1)
    (demo / ".knot.edn").write_text(config, encoding="utf-8")

    checkout = created(
        demo,
        "Checkout in two taps",
        "--type",
        "epic",
        "-p",
        "1",
        "--tags",
        "web,payments",
        "-d",
        "Returning buyers should pay without retyping anything they told us before.",
    )
    search = created(
        demo, "Search that forgives typos", "--type", "epic", "-p", "2", "--tags", "search"
    )
    bug = created(
        demo,
        "Promo code applies twice after a page refresh",
        "--type",
        "bug",
        "-p",
        "0",
        "--tags",
        "payments",
        "--mode",
        "afk",
    )
    saved = created(
        demo,
        "Show saved cards first at checkout",
        "--parent",
        checkout,
        "-p",
        "1",
        "--tags",
        "payments",
        "--assignee",
        "dana",
    )
    created(
        demo, "Autocomplete the delivery address", "--parent", checkout, "-p", "1", "--tags", "web"
    )
    sticky = created(
        demo,
        "Keep the order summary on screen on phones",
        "--parent",
        checkout,
        "-p",
        "2",
        "--tags",
        "web",
        "--assignee",
        "sam",
    )
    created(demo, "Gift card field at checkout", "--parent", checkout, "-p", "2", "--dep", bug)
    created(demo, "Refund a gift card partially", "--parent", checkout, "-p", "3", "--dep", bug)
    created(demo, "Typo-tolerant product search", "--parent", search, "-p", "2", "--mode", "afk")
    boost = created(demo, "Rank in-stock items first", "--parent", search, "-p", "2")
    created(
        demo, "Upgrade the payment SDK", "-p", "1", "--tags", "payments,chore", "--type", "chore"
    )
    created(demo, "Share a wishlist by link", "-p", "3", "--type", "feature", "--tags", "web")
    created(demo, "Rotate the staging certificates", "-p", "2", "--type", "chore", "--mode", "afk")

    knot(
        demo,
        "document",
        "add",
        checkout,
        "--title",
        "Checkout in two taps spec",
        "--type",
        "spec",
        stdin=SPEC,
    )
    knot(
        demo,
        "document",
        "add",
        checkout,
        "--title",
        "Checkout rollout plan",
        "--type",
        "plan",
        stdin=PLAN,
    )
    knot(
        demo,
        "document",
        "add",
        sticky,
        "--title",
        "Sticky summary spec",
        "--type",
        "spec",
        stdin="## Goal\n\nThe total stays visible while a buyer scrolls the cart.\n",
    )
    knot(demo, "update", sticky, "--status", "in_progress")
    knot(
        demo,
        "update",
        saved,
        "--status",
        "closed",
        "--force",
        "--summary",
        "Shipped behind a flag.",
    )
    knot(demo, "update", boost, "--status", "closed", "--force", "--summary", "Shipped.")
    return {"ticket": checkout}


def backdate(demo: Path) -> None:
    """Spread every ticket's times over the last month, newest first, the active one fresh."""
    now = datetime.now(UTC)
    files = sorted((demo / ".tickets").rglob("acme-*.md"))
    for age, path in enumerate(files):
        text = path.read_text(encoding="utf-8")
        fresh = "status: in_progress" in text
        updated = now - (timedelta(hours=2) if fresh else timedelta(days=age * 2 + 1, hours=age))
        created_at = updated - timedelta(days=3)
        for field, when in (("created", created_at), ("updated", updated)):
            stamp = when.strftime("%Y-%m-%dT%H:%M:%S.000000Z")
            text = re.sub(rf"(?m)^{field}: .*$", f"{field}: '{stamp}'", text, count=1)
        path.write_text(text, encoding="utf-8")


def fetched(path: str) -> str:
    """One page of the running demo panel, on loopback."""
    connection = http.client.HTTPConnection("127.0.0.1", PORT, timeout=30)
    try:
        connection.request("GET", path)
        return connection.getresponse().read().decode()
    finally:
        connection.close()


def shot(path: str, file: Path, profile: Path) -> None:
    """A dark-theme screenshot of one page, at the README's width.

    Headless Chrome writes the file once the page has loaded but stays running while the page's
    digest poll does, so it is ended here once the file has stopped growing.
    """
    chrome = subprocess.Popen(  # pylint: disable=consider-using-with
        [
            CHROME,
            "--headless=new",
            f"--user-data-dir={profile}",
            "--no-first-run",
            "--disable-gpu",
            "--force-dark-mode",
            "--blink-settings=preferredColorScheme=0",
            "--hide-scrollbars",
            f"--window-size={WIDTH},{HEIGHT}",
            f"--screenshot={file}",
            f"http://127.0.0.1:{PORT}{path}",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        size = -1
        for _ in range(120):
            time.sleep(0.5)
            now = file.stat().st_size if file.exists() else -1
            if now > 0 and now == size:
                return
            size = now
        sys.exit(f"{path}: Chrome wrote no screenshot within a minute")
    finally:
        chrome.terminate()
        try:
            chrome.wait(timeout=5)
        except subprocess.TimeoutExpired:
            chrome.kill()
            chrome.wait(timeout=5)


def dark(file: Path) -> bool:
    """Whether the screenshot's top-left corner is dark, as the dark theme draws it."""
    with Image.open(file) as image:
        red, green, blue = image.convert("RGB").getpixel((4, 4))
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue < 40


def serve(demo: Path) -> subprocess.Popen:
    """The real knotview over the demo backlog, once it answers."""
    panel = subprocess.Popen(  # pylint: disable=consider-using-with
        ["knotview", "--repository", str(demo), "--port", str(PORT)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(60):
        try:
            fetched("/")
            return panel
        except OSError:
            time.sleep(0.5)
    sys.exit("the demo panel did not answer within half a minute")


def captured(views: dict[str, str], work: Path) -> list[Image.Image]:
    """Each view checked, captured and written as an inline image; the frames for the tour."""
    OUT.mkdir(parents=True, exist_ok=True)
    frames = []
    for view, path in views.items():
        missing(view, fetched(path))
        raw = work / f"{view}.png"
        shot(path, raw, work / f"profile-{view}")
        if not dark(raw):
            sys.exit(f"{view}: the screenshot is not in the dark theme")
        with Image.open(raw) as image:
            frame = image.convert("RGB")
        target = OUT / f"{view}.jpg"
        frame.save(target, "JPEG", quality=82, optimize=True)
        if target.stat().st_size > INLINE_LIMIT:
            frame.save(target, "JPEG", quality=70, optimize=True)
        frames.append(frame.resize((1280, int(frame.height * 1280 / frame.width))))
    return frames


def toured(frames: list[Image.Image]) -> None:
    """The animated tour, and a check that every image keeps to its budget."""
    tour = OUT / "tour.webp"
    frames[0].save(
        tour, "WEBP", save_all=True, append_images=frames[1:], duration=2500, loop=0, quality=70
    )
    for image in (*OUT.glob("*.jpg"), tour):
        limit = TOUR_LIMIT if image == tour else INLINE_LIMIT
        if image.stat().st_size > limit:
            sys.exit(f"{image.name} is {image.stat().st_size} bytes, over {limit}")
    print("\n".join(f"{image.name} {image.stat().st_size}" for image in sorted(OUT.iterdir())))


def main() -> None:
    """Build, serve, check, capture and write every README image."""
    work = Path(tempfile.mkdtemp(prefix="knotview-demo-"))
    demo = work / "acme-shop"
    demo.mkdir()
    panel = None
    try:
        ticket = build(demo)["ticket"]
        backdate(demo)
        owned = knot(demo, "show", ticket)["documents"]
        document = next(one["id"] for one in owned if one["type"] == "spec")
        panel = serve(demo)
        toured(
            captured(
                {
                    "overview": "/",
                    "tickets": "/tickets",
                    "tree": "/tree",
                    "ready": "/queue/ready",
                    "blocked": "/queue/blocked",
                    "ticket": f"/ticket/{ticket}",
                    "document": f"/document/{document}",
                },
                work,
            )
        )
    finally:
        if panel is not None:
            panel.terminate()
            panel.wait(timeout=10)
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
