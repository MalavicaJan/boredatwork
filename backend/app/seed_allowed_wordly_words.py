"""Fill the allowed-guess pool, so Wordly can reject non-words.

    python -m app.seed_wordly_allowed_words
    python -m app.seed_wordly_allowed_words --source /path/to/words.txt

These words are guessable but never chosen as an answer — the same
split Wordle uses. Without them the only valid guesses would be the
daily answers, which would hand the player the solution.

The list is dwyl/english-words (public domain), filtered to five-letter
ASCII words: about 16,000 of them. It is deliberately permissive:
rejecting a real but obscure word annoys players far more than
accepting one does.
"""

import argparse
import urllib.request

from sqlalchemy import func

from app.database import SessionLocal
from app.models.wordly_word import ALLOWED, WordlyWord


WORDS_URL = (
    "https://raw.githubusercontent.com/dwyl/english-words/master/"
    "words_alpha.txt"
)

WORD_LENGTH = 5

# Inserted in chunks: one commit per word would take minutes for 16k
# rows, and one commit for all of them holds a long transaction.
BATCH_SIZE = 500


def read_words(source: str | None) -> list[str]:
    if source:
        with open(source, encoding="utf-8") as handle:
            raw = handle.read()
    else:
        print(f"Downloading {WORDS_URL} ...")

        request = urllib.request.Request(
            WORDS_URL,
            headers={"User-Agent": "boredatwork-seed/1.0"},
        )

        with urllib.request.urlopen(request, timeout=120) as response:
            raw = response.read().decode("utf-8")

    words = {
        word.strip().lower()
        for word in raw.splitlines()
    }

    return sorted(
        word
        for word in words
        if len(word) == WORD_LENGTH and word.isalpha() and word.isascii()
    )


def seed(source: str | None) -> None:
    words = read_words(source)

    print(f"{len(words)} five-letter words in the source")

    db = SessionLocal()

    added = 0
    skipped = 0

    try:
        # One query instead of 16,000: a per-word existence check would
        # dominate the runtime.
        existing = {
            row[0]
            for row in db.query(WordlyWord.word).all()
        }

        pending = []

        for word in words:
            if word in existing:
                # Already a daily answer or a practice word. Leave the
                # pool it is in alone.
                skipped += 1
                continue

            pending.append(WordlyWord(word=word, pool=ALLOWED))

            if len(pending) >= BATCH_SIZE:
                db.add_all(pending)
                db.commit()
                added += len(pending)
                pending = []
                print(f"  {added} added...")

        if pending:
            db.add_all(pending)
            db.commit()
            added += len(pending)

        counts = (
            db.query(WordlyWord.pool, func.count())
            .group_by(WordlyWord.pool)
            .all()
        )
    finally:
        db.close()

    print(f"added {added}, already present {skipped}")

    for pool, count in sorted(counts):
        print(f"  {pool}: {count}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--source",
        default=None,
        help="Path to a local word list, one word per line",
    )

    seed(parser.parse_args().source)


if __name__ == "__main__":
    main()
