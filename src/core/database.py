from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.configs.db_config import db_settings


async_engine = create_async_engine(
    url=db_settings.DATABASE_URL,
    echo=True,
    future=True,
)

async_session = async_sessionmaker(async_engine, expire_on_commit=False)