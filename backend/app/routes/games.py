from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.game_result import GameResult
from app.models.user import User
from app.schemas.game_result import GameResultCreate, GameResultResponse
from app.session import get_current_user


router = APIRouter(
    prefix="/api/v1/games",
    tags=["games"],
)


@router.post(
    "/results",
    response_model=GameResultResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_game_result(
    result: GameResultCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    new_result = GameResult(
        user_id=current_user.id,
        game=result.game,
        score=result.score,
        completed=result.completed,
    )

    db.add(new_result)
    db.commit()
    db.refresh(new_result)

    return new_result
