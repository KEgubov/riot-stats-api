from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_riot_client, get_session
from src.clients.riot_client import RiotClient
from src.schemas.player import (
    ChampionAggregateResponse,
    MatchResponse,
    PlayerProfileResponse,
)
from src.services.player_service import PlayerService

router = APIRouter()


@router.get("/healthz")
async def healthz():
    return {"status": "ok"}


@router.post(
    "/players/{game_name}/{tag_line}/sync", response_model=PlayerProfileResponse
)
async def sync_player(
    game_name: str,
    tag_line: str,
    session: AsyncSession = Depends(get_session),
    riot: RiotClient = Depends(get_riot_client),
):
    service = PlayerService(session, riot)
    player = await service.refresh_player(game_name, tag_line)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found in Riot API")
    return player


@router.get("/players/{game_name}/{tag_line}", response_model=PlayerProfileResponse)
async def get_player(
    game_name: str,
    tag_line: str,
    session: AsyncSession = Depends(get_session),
    riot: RiotClient = Depends(get_riot_client),
):
    service = PlayerService(session, riot)
    player = await service.get_profile(game_name, tag_line)
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    return player


@router.get(
    "/players/{game_name}/{tag_line}/matches", response_model=list[MatchResponse]
)
async def get_matches(
    game_name: str,
    tag_line: str,
    limit: int = 20,
    session: AsyncSession = Depends(get_session),
    riot: RiotClient = Depends(get_riot_client),
):
    service = PlayerService(session, riot)
    return await service.get_matches(game_name, tag_line, limit)


@router.get(
    "/players/{game_name}/{tag_line}/champions",
    response_model=list[ChampionAggregateResponse],
)
async def get_champions(
    game_name: str,
    tag_line: str,
    session: AsyncSession = Depends(get_session),
    riot: RiotClient = Depends(get_riot_client),
):
    service = PlayerService(session, riot)
    return await service.get_champion_aggregates(game_name, tag_line)
