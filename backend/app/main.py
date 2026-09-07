from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import settings
from app.models.sequence import SequenceChallenge  # noqa: F401
from app.models.sequence_result import SequenceResult  # noqa: F401
from app.models.sudoku import SudokuPuzzle  # noqa: F401
from app.models.wordly_attempt import WordlyAttempt  # noqa: F401
from app.models.blackout import BlackoutArticle, BlackoutChallenge  # noqa: F401
from app.routes.blackout import router as blackout_router
from app.routes.games import router as games_router
from app.routes.sequence import router as sequence_router
from app.routes.sudoku import router as sudoku_router
from app.routes.users import router as users_router
from app.routes.wordly import router as wordly_router

app = FastAPI(
    title="boredatwork.xyz API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(users_router)
app.include_router(games_router)
app.include_router(wordly_router)
app.include_router(sequence_router)
app.include_router(sudoku_router)
app.include_router(blackout_router)

@app.get("/api/v1/health")
def health_check():
    return {"status": "ok"}
