from fastapi import FastAPI

from src.api.routes import router
from src.clients.riot_client import RiotClient

app = FastAPI(title='Riot Stats API')
app.include_router(router)

riot_client = RiotClient()

@app.on_event('startup')
async def startup() -> None:
    await riot_client.connect()

@app.on_event('shutdown')
async def shutdown() -> None:
    await riot_client.disconnect()
