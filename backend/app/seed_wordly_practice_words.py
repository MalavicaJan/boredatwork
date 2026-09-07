"""Fill the practice word pool.

    python -m app.seed_wordly_practice_words

Practice words are deliberately a different set from the daily answers
(see the note on the WordlyWord model). A word already present in the
daily pool is skipped rather than moved.
"""

from app.database import SessionLocal
from app.models.wordly_word import DAILY, PRACTICE, WordlyWord


WORDS = [
    "about", "above", "actor", "acute", "adopt", "after", "again", "agent",
    "agree", "album", "alert", "alike", "alive", "alley", "allow", "alone",
    "along", "amber", "angle", "angry", "ankle", "apart", "arena", "argue",
    "arise", "armor", "aroma", "arrow", "aside", "asset", "audio", "avoid",
    "awake", "award", "aware", "badge", "baker", "basic", "basin", "beach",
    "beard", "beast", "began", "begin", "being", "belly", "below", "bench",
    "berry", "birth", "black", "blade", "blame", "blank", "blast", "blaze",
    "bleak", "blend", "bless", "blind", "block", "bloom", "board", "boast",
    "bonus", "boost", "booth", "bound", "brave", "bread", "break", "breed",
    "brief", "bring", "brisk", "broad", "brown", "brush", "build", "built",
    "bunch", "burnt", "cabin", "cable", "candy", "canoe", "cargo", "carve",
    "catch", "cause", "cease", "chalk", "charm", "chart", "chase", "cheap",
    "check", "chess", "chest", "chief", "child", "chill", "choir", "chose",
    "civic", "claim", "clash", "class", "clean", "clear", "clerk", "click",
    "cliff", "climb", "cloak", "clock", "close", "cloth", "cloud", "coast",
    "cobra", "cocoa", "colon", "color", "coral", "couch", "cough", "could",
    "count", "court", "cover", "crack", "craft", "crane", "crash", "crawl",
    "crazy", "cream", "creek", "crest", "crime", "crisp", "cross", "crowd",
    "crown", "crumb", "crush", "curve", "cycle", "daily", "dance", "dated",
    "dealt", "debut", "decay", "delay", "dense", "depth", "diary", "digit",
    "dirty", "ditch", "dodge", "doubt", "dozen", "draft", "drain", "drama",
    "drawn", "dress", "dried", "drift", "drink", "drive", "drove", "drown",
    "eager", "eagle", "early", "earth", "eight", "elbow", "elder", "elite",
    "empty", "enemy", "enjoy", "enter", "entry", "equal", "equip", "error",
    "essay", "event", "every", "exact", "exist", "extra", "fable", "faith",
    "false", "fancy", "fatal", "fault", "favor", "feast", "fence", "ferry",
    "fever", "fiber", "field", "fiery", "fifth", "fifty", "fight", "final",
    "first", "flame", "flash", "fleet", "flesh", "flint", "float", "flock",
    "flood", "floor", "flour", "fluid", "flute", "focus", "force", "forge",
    "forth", "forty", "forum", "found", "frame", "fraud", "fresh", "front",
    "frost", "fruit", "fully", "funny", "ghost", "giant", "given", "glass",
    "gleam", "globe", "glory", "glove", "grace", "grade", "grain", "grand",
    "grant", "grape", "graph", "grasp", "grass", "grave", "great", "greet",
    "grief", "grill", "gross", "group", "grove", "guard", "guess", "guest",
    "guide", "guilt", "habit", "happy", "harsh", "haunt", "heart", "heavy",
    "hedge", "hello", "hence", "hobby", "honey", "honor", "horse", "hotel",
    "hound", "human", "humor", "hurry", "ideal", "image", "imply", "index",
    "inner", "input", "irony", "issue", "ivory", "jelly", "jewel", "joint",
    "judge", "juice", "knife", "knock", "known", "label", "labor", "large",
    "laser", "later", "laugh", "layer", "learn", "lease", "least", "leave",
    "legal", "lemon", "level", "lever", "limit", "linen", "liver", "lobby",
    "local", "lodge", "logic", "loose", "lower", "loyal", "lucky", "lunar",
    "lunch", "lyric", "magic", "major", "maker", "maple", "march", "marsh",
    "match", "maybe", "mayor", "medal", "media", "mercy", "merit", "metal",
    "meter", "midst", "might", "minor", "minus", "mixed", "model", "moist",
    "money", "month", "moral", "motor", "mount", "mouse", "mouth", "movie",
    "muddy", "nasty", "nerve", "never", "newly", "night", "noble", "noise",
    "north", "novel", "nurse", "occur", "ocean", "offer", "often", "olive",
    "onion", "onset", "opera", "orbit", "order", "organ", "other", "ought",
    "outer", "owner", "paint", "panel", "panic", "paper", "party", "pasta",
    "patch", "pause", "peace", "peach", "pearl", "pedal", "penny", "phase",
    "phone", "photo", "piano", "piece", "pilot", "pinch", "pitch", "pivot",
    "pixel", "place", "plain", "plane", "plate", "plaza", "point", "polar",
    "porch", "pound", "power", "press", "price", "pride", "prime", "print",
    "prior", "prize", "probe", "proof", "proud", "prove", "pulse", "punch",
    "pupil", "purse", "queen", "query", "quest", "queue", "quick", "quiet",
    "quilt", "quite", "quota", "radar", "radio", "raise", "rally", "ranch",
    "range", "rapid", "ratio", "razor", "reach", "ready", "realm", "rebel",
    "refer", "reign", "relax", "relay", "renew", "reply", "rider", "ridge",
    "rifle", "rigid", "rinse", "risky", "rival", "roast", "robin", "robot",
    "rocky", "roman", "rough", "round", "route", "royal", "rugby", "ruler",
    "rumor", "rural", "salad", "salon", "sauce", "scale", "scare", "scene",
    "scope", "score", "scout", "scrap", "sense", "serve", "seven", "shade",
    "shaft", "shake", "shall", "shame", "shape", "share", "shark", "sharp",
    "sheep", "sheet", "shelf", "shell", "shift", "shine", "shirt", "shock",
    "shore", "short", "shout", "shown", "sight", "silly", "since", "siren",
    "sixth", "skill", "skirt", "slate", "sleep", "slice", "slide", "slope",
    "small", "smart", "smoke", "snack", "snake", "solar", "solid", "solve",
    "sorry", "sound", "south", "spare", "spark", "speak", "spear", "speed",
    "spell", "spend", "spice", "spike", "spine", "spite", "split", "spoke",
    "spoon", "sport", "spray", "squad", "stack", "staff", "stage", "stair",
    "stake", "stall", "stamp", "stand", "stare", "start", "state", "steam",
    "steel", "steep", "steer", "stern", "stick", "stiff", "still", "sting",
    "stock", "stone", "stool", "store", "storm", "story", "stove", "strap",
    "straw", "strip", "stuck", "study", "stuff", "style", "sugar", "suite",
    "sunny", "super", "surge", "sweat", "sweep", "sweet", "swept", "swift",
    "swing", "sword", "syrup", "taken", "tally", "taste", "teach",
    "tempo", "tenth", "thank", "theft", "theme", "there", "thick", "thief",
    "thing", "think", "third", "thorn", "those", "three", "throw", "thumb",
    "tiger", "tight", "timer", "tired", "title", "toast", "today", "token",
    "tooth", "topic", "torch", "total", "touch", "tough", "tower", "toxic",
    "trace", "track", "trade", "trail", "trait", "trash", "treat", "trend",
    "trial", "tribe", "trick", "troop", "trout", "truck", "truly", "trunk",
    "trust", "truth", "twice", "twist", "ultra", "uncle", "under", "union",
    "unite", "unity", "until", "upper", "upset", "urban", "usage", "usual",
    "vague", "valid", "value", "valve", "vapor", "vault", "venue", "verse",
    "video", "villa", "vinyl", "viral", "virus", "visit", "vital", "vivid",
    "vocal", "voice", "voter", "wagon", "waist", "waste", "watch", "wheat",
    "wheel", "where", "which", "while", "white", "whole", "whose", "widen",
    "wider", "widow", "width", "windy", "witch", "woman", "worry", "worse",
    "worst", "worth", "would", "wound", "wrist", "write", "wrong", "yacht",
    "yield", "young", "youth", "zebra",
]


def seed() -> None:
    db = SessionLocal()

    added = 0
    skipped = 0

    try:
        for word in sorted(set(WORDS)):
            if len(word) != 5 or not word.isalpha():
                print(f"skipping malformed word: {word!r}")
                continue

            existing = (
                db.query(WordlyWord)
                .filter(WordlyWord.word == word)
                .first()
            )

            if existing:
                # Already a daily answer: leave the pools separate.
                skipped += 1
                continue

            db.add(WordlyWord(word=word, pool=PRACTICE))
            added += 1

        db.commit()
    finally:
        db.close()

    daily = db_count(DAILY)
    practice = db_count(PRACTICE)

    print(f"added {added}, skipped {skipped}")
    print(f"pools: {daily} daily, {practice} practice")


def db_count(pool: str) -> int:
    db = SessionLocal()

    try:
        return (
            db.query(WordlyWord)
            .filter(WordlyWord.pool == pool)
            .count()
        )
    finally:
        db.close()


if __name__ == "__main__":
    seed()
