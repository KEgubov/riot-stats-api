from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.api.exception_handlers import register_exception_handlers
from src.api.routes import router
from src.clients.riot_client import RiotClient

riot_client = RiotClient()


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting up: connecting to Riot API Client...")
    await riot_client.connect()

    yield

    print("Shutting down: disconnecting Riot API Client...")
    await riot_client.disconnect()


app = FastAPI(title="Riot Stats API", lifespan=lifespan)

app.include_router(router)
register_exception_handlers(app)
