import asyncio
import urllib.parse
from typing import Any, Optional

import httpx

from src.clients.exceptions import RiotKeyExpiredError
from src.configs.api_config import settings
from src.schemas.riot import (
    RiotAccountSchema,
    RiotLeagueSchema,
    RiotMatchResponseSchema,
)


class RiotClient:
    """
    An asynchronous HTTP client wrapper for the Riot Games API.
    Handles rate-limiting (429), server errors (5xx), and automatically
    validates responses into Pydantic schemas.
    """

    EUROPE_URL = "https://europe.api.riotgames.com"
    EUW1_URL = "https://euw1.api.riotgames.com"

    def __init__(self):
        self.client: httpx.AsyncClient | None = None

    async def connect(self) -> None:
        """
        Initializes a single persistent AsyncClient session instance.
        :return: None
        """
        self.client = httpx.AsyncClient(
            headers={"X-Riot-Token": settings.api_key},
            timeout=10.0,  # Custom timeout to avoid false-positive timeouts
        )

    async def disconnect(self) -> None:
        """
        Closes the underlying persistent HTTP client session.
        :return: None
        """
        if self.client:
            await self.client.aclose()

    async def _request(self, method: str, url: str, **kwargs: Any) -> Optional[Any]:
        """
        Internal helper to execute HTTP requests with retry logic for 429 and 5xx.
        Returns parsed JSON or None if 404 is encountered.
        :param method: str
        :param url: str
        :param kwargs: Any
        :return: Optional[Any]
        """
        if not self.client:
            raise RuntimeError("RiotClient is not connected. Call connect() first.")

        for attempt in range(3):
            response = await self.client.request(method, url, **kwargs)

            # Handle 403 Forbidden (Key expired) - Fail Fast as per requirements
            if response.status_code == 403:
                raise RiotKeyExpiredError(
                    "Riot API Key has expired or is invalid. Please update your "
                    "environment variables."
                )

            # Handle 404 Not Found gracefully (e.g., player or match doesn't exist)
            if response.status_code == 404:
                return None

            # Handle 429 Rate Limit - respect Retry-After header
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 5))
                await asyncio.sleep(retry_after + 1)
                continue

            # Handle 5xx Server Errors - exponential backoff retry
            if response.status_code >= 500:
                await asyncio.sleep(2**attempt)
                continue

            # Raise for any other HTTP errors (e.g., 400, 401)
            response.raise_for_status()
            return response.json()

        # If all attempts failed due to 429/5xx, raise the final status
        response.raise_for_status()

    async def get_account_by_riot_id(
        self, game_name: str, tag_line: str
    ) -> RiotAccountSchema | None:
        """
        Resolves a player's Riot ID (gameName#tagLine) to a cross-regional PUUID.
        Endpoint: /riot/account/v1/accounts/by-riot-id/{gameName}/{tagLine}
        :param game_name: str
        :param tag_line: str
        :return: RiotAccountSchema
        """
        safe_game_name = urllib.parse.unquote(game_name)
        safe_tag_line = urllib.parse.quote(tag_line)
        url = f"{self.EUROPE_URL}/riot/account/v1/accounts/by-riot-id/{safe_game_name}/{safe_tag_line}"
        data = self._request("GET", url)
        if not data:
            return None
        return RiotAccountSchema.model_validate(data, from_attributes=True)

    async def get_matches_by_puuid(
        self, puuid: str, start: int = 0, count: int = 20
    ) -> list[str]:
        """
        Fetches a list of match IDs for a specific player's PUUID.
        Filters strictly by SoloQ (queue 420) as requested.
        Endpoint: /lol/match/v5/matches/by-puuid/{puuid}/ids
        :param puuid: str
        :param start: int=0
        :param count: int=20
        :return: list[str]
        """
        url = f"{self.EUROPE_URL}/lol/match/v5/matches/by-puuid/{puuid}/ids"
        params = {"queue": 420, "start": start, "count": count}
        data = await self._request("GET", url, params=params)
        return data if data is not None else []

    async def get_match_by_id(self, match_id: str) -> RiotMatchResponseSchema | None:
        """
        Fetches detailed game data for a specific match ID.
        Endpoint: /lol/match/v5/matches/{matchId}
        :param match_id: str
        :return: Optional[RiotMatchResponseSchema]
        """
        url = f"{self.EUROPE_URL}/lol/match/v5/matches/{match_id}"
        data = await self._request("GET", url)
        if not data:
            return None
        return RiotMatchResponseSchema.model_validate(data)

    async def get_league_entries_by_puuid(self, puuid: str) -> list[RiotLeagueSchema]:
        """
        Fetches ranked positions (SoloQ, Flex) for a given player's PUUID.
        Endpoint: /lol/league/v4/entries/by-puuid/{puuid}
        :param puuid: str
        :return: list[RiotLeagueSchema]
        """
        url = f"{self.EUW1_URL}/lol/league/v4/entries/by-puuid/{puuid}"
        data = await self._request("GET", url)
        if not data:
            return []
        return [
            RiotLeagueSchema.model_validate(entry, from_attributes=True)
            for entry in data
        ]
