from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from starlette import status

from src.api.deps import get_player_service
from src.schemas.player import (
    ChampionAggregateResponse,
    MatchResponse,
    PlayerProfileResponse,
    SyncAcceptedResponse,
)
from src.services.player_service import PlayerService

router = APIRouter()


@router.get("/healthz")
async def healthz() -> dict:
    """
    Returns healthz status
    :return: dict
    """
    return {"status": "ok"}


@router.post(
    "/players/{game_name}/{tag_line}/sync",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SyncAcceptedResponse,
)
async def sync_player(
    game_name: str,
    tag_line: str,
    background_tasks: BackgroundTasks,
    service: PlayerService = Depends(get_player_service),
):
    background_tasks.add_task(
        service.refresh_player,
        game_name=game_name,
        tag_line=tag_line,
    )
    return SyncAcceptedResponse(
        message="Player synchronization started in the background",
        game_name=game_name,
        tag_line=tag_line,
    )


@router.get(
    "/players/{game_name}/{tag_line}",
    status_code=status.HTTP_200_OK,
    response_model=PlayerProfileResponse,
)
async def get_player(
    game_name: str,
    tag_line: str,
    service: PlayerService = Depends(get_player_service),
):
    player = await service.get_profile(game_name, tag_line)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.get(
    "/players/{game_name}/{tag_line}/matches",
    status_code=status.HTTP_200_OK,
    response_model=list[MatchResponse],
)
async def get_matches(
    game_name: str,
    tag_line: str,
    limit: int = 20,
    service: PlayerService = Depends(get_player_service),
):
    return await service.get_matches(game_name, tag_line, limit)


@router.get(
    "/players/{game_name}/{tag_line}/champions",
    status_code=status.HTTP_200_OK,
    response_model=list[ChampionAggregateResponse],
)
async def get_champions(
    game_name: str,
    tag_line: str,
    service: PlayerService = Depends(get_player_service),
):
    return await service.get_champion_aggregates(game_name, tag_line)
