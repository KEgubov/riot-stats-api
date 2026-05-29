from collections.abc import AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.riot_client import RiotClient
from src.core.database import async_session
from src.services.player_service import PlayerService


async def get_session() -> AsyncGenerator:
    async with async_session() as session:
        yield session


def get_riot_client() -> RiotClient:
    from src.main import riot_client
    return riot_client


async def get_player_service(
    session: AsyncSession = Depends(get_session),
    riot: RiotClient = Depends(get_riot_client),
) -> PlayerService:
    return PlayerService(session, riot)
