import asyncio
import urllib.parse
from typing import Any

import httpx

from src.configs.api_config import settings


class RiotClient:
    EUROPE_URL = "https://europe.api.riotgames.com"
    EUW1_URL = "https://euw1.api.riotgames.com"

    def __init__(self):
        self.client: httpx.AsyncClient | None = None

    async def connect(self):
        self.client = httpx.AsyncClient(
            headers={"X-Riot-Token": settings.api_key},
            timeout=10.0,
        )

    async def disconnect(self):
        if self.client:
            await self.client.aclose()

    async def _request(self, method: str, url: str, **kwargs) -> Any:
        if not self.client:
            raise RuntimeError("RiotClient is not connected. Call connect() first.")

        for attempt in range(3):
            response = await self.client.request(method, url, **kwargs)

            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                await asyncio.sleep(retry_after + 1)
                continue

            if response.status_code >= 500:
                await asyncio.sleep(2**attempt)
                continue

            response.raise_for_status()
            return response.json()

        response.raise_for_status()

    async def get_account_by_riot_id(
        self, game_name: str, tag_line: str
    ) -> dict[str, Any]:
        """
        /riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}
        :param: game_name: str
        :param: tag_line: str
        :return: dict[str, Any]
        """
        safe_tag_line = urllib.parse.quote(tag_line)
        url = f"{self.EUROPE_URL}/riot/account/v1/accounts/by-riot-id/{game_name}/{safe_tag_line}"
        return await self._request("GET", url)

    async def get_matches_by_puuid(
        self, puuid: str, start: int = 0, count: int = 20
    ) -> list[str]:
        url = f"{self.EUROPE_URL}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {"queue": 420, "start": start, "count": count}
        return await self._request("GET", url, params=params)

    async def get_match_by_id(self, match_id: str) -> dict[str, Any]:
        url = f"{self.EUROPE_URL}/lol/match/v5/matches/{match_id}"
        return await self._request("GET", url)

    async def get_league_entries_by_puuid(self, puuid: str) -> list[dict[str, Any]]:
        url = f"{self.EUW1_URL}/lol/league/v4/entries/by-puuid/{puuid}"
        return await self._request("GET", url)

async def main():
    riot_client = RiotClient()

    await riot_client.connect()

    try:
        # stats = await riot_client.get_league_entries_by_puuid('bsopDeAgsNfaA8ng3zFpwV3elOvuPzvWtrVA_RlBBRnJmTS70sVogJKxg9n-ssituCfZvbpUMKvj6w')
        # matches = await riot_client.get_matches_by_puuid('bsopDeAgsNfaA8ng3zFpwV3elOvuPzvWtrVA_RlBBRnJmTS70sVogJKxg9n-ssituCfZvbpUMKvj6w')
        match = await riot_client.get_match_by_id('EUW1_7866358785')
        # print(stats)
        # print(matches)
        print(match)
    finally:
        await riot_client.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
