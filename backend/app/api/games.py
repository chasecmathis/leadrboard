from fastapi import APIRouter, Depends, status, HTTPException
from app.models import User, Game
from app.core.security import get_current_user
from app.db.session import get_session
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
import app.common_types as types
from app.services.recommendation import GameRecommendation

router = APIRouter(prefix="/games", tags=["Games"])


@router.get(
    "/{game_id}", response_model=Game, description="Returns the corresponding game"
)
async def get_game(
    game_id: int,
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.exec(select(Game).where(Game.id == game_id))
    game = result.first()
    if not game:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Game not found"
        )

    return game


@router.get(
    "/", response_model=list[Game], description="Returns a corresponding list of games"
)
async def get_games(
    skip: int = 0,
    limit: int = 10,
    sort_by: types.GameSortBy = types.GameSortBy.ID,
    sort_dir: types.SortDirection = types.SortDirection.ASCENDING,
    _current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    if skip < 0 or limit < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parameters"
        )

    sort_attr = getattr(Game, sort_by)

    statement = select(Game).offset(skip).limit(limit)
    if sort_dir == types.SortDirection.ASCENDING:
        statement = statement.order_by(sort_attr.asc())
    else:
        statement = statement.order_by(sort_attr.desc())
    result = await session.exec(statement)
    games = result.all()
    return games

@router.get("/discover/personalized", response_model=list[Game])
async def get_personalized_games(
    limit: int = 10,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if limit < 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parameters")

    recommender = GameRecommendation(session)
    game_ids = await recommender.generate_recommendations(target_user_id=current_user.id, num_recommendations=limit)

    if not game_ids:
        fallback_statement = select(Game).limit(limit)
        result = await session.exec(fallback_statement)
        return result.all()

    statement = select(Game).where(Game.id.in_(game_ids))
    result = await session.exec(statement)
    games = result.all()

    return games

