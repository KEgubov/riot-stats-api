import asyncio

from src.core.database import async_engine
from src.models.base_models import Base

async def create_tables() -> None:
    """
    The function creates tables in the database.
    If you need to recreate the current tables,
    then you can use drop all first
    :return: None
    """
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(create_tables())