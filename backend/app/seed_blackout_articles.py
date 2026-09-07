"""Import Wikipedia lead sections for the Blackout game.

    python -m app.seed_blackout_articles
    python -m app.seed_blackout_articles --limit 20

Uses the Wikimedia REST summary endpoint, which returns exactly the lead
section. Wikimedia's policy requires a descriptive User-Agent with a
contact address, so set BLACKOUT_USER_AGENT before running this against
the live API.

Wikipedia text is CC BY-SA 4.0. The article URL is stored with every
row and shown to the player once the puzzle ends, which is what the
licence's attribution requirement needs.
"""

import argparse
import os
import time
import urllib.parse
import urllib.request
import json

from app.database import SessionLocal
from app.models.blackout import BlackoutArticle


# The REST summary endpoint only returns the lead section. The action
# API with prop=extracts returns the whole article as plain text, which
# is what the game needs.
API_URL = "https://en.wikipedia.org/w/api.php"
SUMMARY_URL = "https://en.wikipedia.org/api/rest_v1/page/summary/"

USER_AGENT = os.environ.get(
    "BLACKOUT_USER_AGENT",
    "boredatwork/1.0 (https://boredatwork.xyz; contact@example.com)",
)

# Recognisable subjects with a decent lead paragraph. Short enough to
# solve in a few minutes, well known enough to be guessable.
TITLES = [
    "Coffee", "Volcano", "Bicycle", "Penguin", "Lighthouse", "Origami",
    "Chess", "Honey", "Piano", "Desert", "Glacier", "Telescope",
    "Bridge", "Sunflower", "Whale", "Compass", "Windmill", "Butterfly",
    "Umbrella", "Guitar", "Rainbow", "Pyramid", "Elephant", "Library",
    "Diamond", "Kangaroo", "Waterfall", "Balloon", "Octopus", "Violin",
    "Camel", "Aquarium", "Anchor", "Bamboo", "Cactus", "Dolphin",
    "Eclipse", "Falcon", "Geyser", "Harbor", "Iceberg", "Jungle",
    "Kite", "Lantern", "Marble", "Nebula", "Orchid", "Parachute",
    "Quartz", "Reef", "Sailboat", "Tornado", "Vineyard", "Walnut",
]

# Full articles, so the floor is about having enough to work with and
# the ceiling is about payload size: every word becomes a token in the
# JSON response and a span in the DOM. 1500 words is roughly 300KB.
MIN_WORDS = 120
MAX_WORDS = 250


def fetch_json(url: str, title: str) -> dict | None:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as error:
        print(f"  {title}: fetch failed ({error})")
        return None


def clean_extract(raw: str, max_words: int) -> str:
    """Plain-text extracts carry '== Section ==' headings and trailing
    boilerplate sections. Strip the markers, drop the reference matter,
    and cut to length on a paragraph boundary."""
    skip_from = (
        "See also",
        "References",
        "Further reading",
        "External links",
        "Notes",
        "Bibliography",
    )

    paragraphs = []
    words = 0

    for block in raw.split("\n"):
        block = block.strip()

        if not block:
            continue

        if block.startswith("="):
            heading = block.strip("= ").strip()

            if heading in skip_from:
                break

            # Keep the heading as its own line of hidden words.
            paragraphs.append(heading)
            continue

        paragraphs.append(block)
        words += len(block.split())

        if words >= max_words:
            break

    return "\n\n".join(paragraphs)


def fetch_article(title: str, max_words: int) -> dict | None:
    """Full article text, plus the canonical title and URL."""
    parameters = urllib.parse.urlencode(
        {
            "action": "query",
            "prop": "extracts",
            "explaintext": "1",
            "redirects": "1",
            "format": "json",
            "formatversion": "2",
            "titles": title,
        }
    )

    payload = fetch_json(f"{API_URL}?{parameters}", title)

    if not payload:
        return None

    pages = payload.get("query", {}).get("pages", [])

    if not pages or pages[0].get("missing"):
        print(f"  {title}: no such article")
        return None

    page = pages[0]

    text = clean_extract(page.get("extract") or "", max_words)

    if not text:
        return None

    canonical = page.get("title") or title

    return {
        "title": canonical,
        "text": text,
        "url": (
            "https://en.wikipedia.org/wiki/"
            + urllib.parse.quote(canonical.replace(" ", "_"))
        ),
    }


def import_articles(
    limit: int | None,
    min_words: int,
    max_words: int,
) -> None:
    db = SessionLocal()

    added = 0
    skipped = 0
    rejected = 0

    try:
        for title in TITLES[:limit]:
            existing = (
                db.query(BlackoutArticle)
                .filter(BlackoutArticle.title == title)
                .first()
            )

            if existing:
                skipped += 1
                continue

            article = fetch_article(title, max_words)

            # Be a polite API client.
            time.sleep(0.3)

            if not article:
                continue

            word_count = len(article["text"].split())

            if word_count < min_words:
                rejected += 1
                print(f"  {title}: only {word_count} words, too short")
                continue

            db.add(
                BlackoutArticle(
                    title=article["title"],
                    lead=article["text"],
                    source_url=article["url"],
                )
            )

            db.commit()

            added += 1
            print(f"  {title}: {word_count} words")

        total = db.query(BlackoutArticle).count()
    finally:
        db.close()

    print(
        f"added {added}, already present {skipped}, "
        f"rejected on length {rejected}, pool now {total}"
    )

    if total == 0:
        print(
            "\nThe pool is empty, so the game will return 503. Try a lower "
            "floor, e.g. --min-words 60"
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--min-words", type=int, default=MIN_WORDS)
    parser.add_argument("--max-words", type=int, default=MAX_WORDS)

    arguments = parser.parse_args()

    import_articles(
        arguments.limit,
        arguments.min_words,
        arguments.max_words,
    )


if __name__ == "__main__":
    main()
