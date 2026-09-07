from app.database import SessionLocal
from app.models.wordly_word import WordlyWord


WORDS = [
    "apple",
    "brain",
    "chair",
    "dream",
    "house",
    "light",
    "music",
    "plant",
    "river",
    "smile",
    "space",
    "table",
    "train",
    "water",
    "world",
]


db = SessionLocal()

try:
    for word in WORDS:
        existing_word = (
            db.query(WordlyWord)
            .filter(WordlyWord.word == word)
            .first()
        )

        if not existing_word:
            db.add(WordlyWord(word=word))

    db.commit()

    print("Wordly words seeded successfully")

finally:
    db.close()
