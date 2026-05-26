from collections.abc import AsyncGenerator

from src.clients.riot_client import RiotClient
from src.core.database import async_session


async def get_session() -> AsyncGenerator:
    async with async_session() as session:
        yield session


def get_riot_client() -> RiotClient:
    from src.main import riot_client
    return riot_client
