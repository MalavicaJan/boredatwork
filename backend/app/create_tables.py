from app.database import Base, engine

# Every model must be imported so it is registered on Base.metadata.
# A model missing from this list is a table that never gets created on
# a fresh database.
from app.models.user import User  # noqa: F401
from app.models.session import UserSession  # noqa: F401
from app.models.game_result import GameResult  # noqa: F401
from app.models.wordly import WordlyChallenge  # noqa: F401
from app.models.wordly_word import WordlyWord  # noqa: F401
from app.models.wordly_guess import WordlyGuess  # noqa: F401
from app.models.sequence import SequenceChallenge  # noqa: F401
from app.models.sequence_result import SequenceResult  # noqa: F401
from app.models.sudoku import SudokuPuzzle  # noqa: F401
from app.models.blackout import BlackoutArticle  # noqa: F401
from app.models.blackout import BlackoutChallenge  # noqa: F401


Base.metadata.create_all(bind=engine)

print("Database tables created successfully!")
