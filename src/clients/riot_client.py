import asyncio
import logging
import urllib.parse
from typing import Any, Optional

import httpx

from src.clients.exceptions import RiotKeyExpiredError, \
    RiotServiceUnavailableException, RiotRateLimitException
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

            import asyncio
            from typing import Any, Optional
            import httpx

    async def _request(self, method: str, url: str, **kwargs: Any) \
        -> Optional[Any]:
        """
        Internal helper to execute HTTP requests with retry logic for 429 and 5xx.
        Returns parsed JSON or None if 404 is encountered.
        """
        if not self.client:
            raise RuntimeError("RiotClient is not connected. Call connect() first.")

        max_attempts = 3

        for attempt in range(max_attempts):
            try:
                response = await self.client.request(method, url, **kwargs)
            except (
                httpx.ConnectError,
                httpx.ConnectTimeout,
                httpx.ReadTimeout,
            ) as next_exc:
                logging.warning(
                    f"Сетевая ошибка при запросе к Riot API "
                    f"({type(next_exc).__name__}). "
                    f"Попытка {attempt + 1}/{max_attempts}."
                )
                if attempt < max_attempts - 1:
                    await asyncio.sleep(2**attempt)
                    continue
                raise RiotServiceUnavailableException(
                    message="The Riot authorization server is temporarily "
                            "unavailable. Network problem.",
                    error_code="SERVICE_UNAVAILABLE",
                )

            # 1. We immediately process a successful response -
            # this is the main scenario (Happy Path)
            if response.status_code == 200:
                return response.json()

            # 2. Processing specific status codes (Fail Fast Graceful)
            if response.status_code == 403:
                raise RiotKeyExpiredError(
                    message="Riot API Key has expired or is invalid. "
                            "Please update your environment variables.",
                    error_code="RIOT_KEY_EXPIRED",
                )

            if response.status_code == 404:
                return None

            # 3. Processing retrays (429 and 5xx)
            if attempt < max_attempts - 1:
                if response.status_code == 429:
                    retry_after = int(response.headers.get("Retry-After", 5))
                    # Adding +1 second is a great practice
                    # to ensure you get past the window.
                    await asyncio.sleep(retry_after + 1)
                    continue

                if response.status_code >= 500:
                    await asyncio.sleep(2**attempt)
                    continue

            # 4. If we got here and this was the last attempt
            # (or the error code is not 4295xx404)
            if response.status_code == 429:
                raise RiotRateLimitException(
                    message="The limit for requests to the gaming service "
                            "has been exceeded. "
                            "Please try again later.",
                    error_code="TOO_MANY_REQUESTS",
                )
            if response.status_code >= 500:
                raise RiotServiceUnavailableException(
                    message="The Riot game server returned an internal error.",
                    error_code="SERVER_ERROR",
                )
            # httpx itself will throw the correct exception
            # (for example, httpx.HTTPStatusError)
            response.raise_for_status()
        return None

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
        safe_game_name = urllib.parse.quote(game_name)
        safe_tag_line = urllib.parse.quote(tag_line)
        url = (f"{self.EUROPE_URL}/riot/account/v1/accounts/by-riot-id/"
               f"{safe_game_name}/{safe_tag_line}")
        data = await self._request("GET", url)
        if not data:
            return None
        return RiotAccountSchema.model_validate(data)

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

    async def get_match_by_id(self, match_id: str) \
        -> RiotMatchResponseSchema | None:
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

    async def get_league_entries_by_puuid(self, puuid: str) \
        -> list[RiotLeagueSchema]:
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
        return [RiotLeagueSchema.model_validate(entry) for entry in data]
