from datetime import datetime
from pydantic import BaseModel


class GameResultCreate(BaseModel):
    game: str
    score: int
    completed: bool = True


class GameResultResponse(BaseModel):
    id: int
    game: str
    score: int
    completed: bool
    played_at: datetime

    model_config = {
        "from_attributes": True
    }
