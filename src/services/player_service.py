from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.riot_client import RiotClient
from src.repositories.player_repository import PlayerRepository
from src.schemas.player import ChampionAggregateResponse


class PlayerService:
    def __init__(self, session: AsyncSession, riot: RiotClient):
        self.repo = PlayerRepository(session)
        self.session = session
        self.riot = riot

    async def resolve_player(self, game_name: str, tag_line: str):
        account = await self.riot.get_account_by_riot_id(game_name, tag_line)
        if not account:
            return None
        await self.repo.upsert_player(
            account.puuid, account.game_name, account.tag_line
        )
        await self.session.commit()
        return await self.repo.get_profile(account.puuid)

    async def refresh_player(
        self, game_name: str, tag_line: str, match_depth: int = 20
    ):
        account = await self.riot.get_account_by_riot_id(game_name, tag_line)
        if not account:
            return None
        await self.repo.upsert_player(
            account.puuid, account.game_name, account.tag_line
        )
        leagues = await self.riot.get_league_entries_by_puuid(account.puuid)
        await self.repo.replace_leagues(account.puuid, leagues)

        match_ids = await self.riot.get_matches_by_puuid(
            account.puuid, count=match_depth
        )
        existing = await self.repo.existing_match_ids(match_ids)
        for mid in match_ids:
            if mid in existing:
                continue
            match = await self.riot.get_match_by_id(mid)
            if match:
                await self.repo.save_match(match)
        await self.session.commit()
        return await self.repo.get_profile(account.puuid)

    async def get_profile(self, game_name: str, tag_line: str):
        player = await self.repo.get_by_riot_id(game_name, tag_line)
        if not player:
            return None
        return await self.repo.get_profile(player.puuid)

    async def get_matches(self, game_name: str, tag_line: str, limit: int = 20):
        player = await self.repo.get_by_riot_id(game_name, tag_line)
        if not player:
            return []
        return await self.repo.recent_matches_for_player(player.puuid, limit)

    async def get_champion_aggregates(self, game_name: str, tag_line: str):
        player = await self.repo.get_by_riot_id(game_name, tag_line)
        if not player:
            return []
        rows = await self.repo.champion_aggregates(player.puuid)
        data = []
        for r in rows:
            deaths = r["deaths"] or 0
            kda = ((r["kills"] or 0) + (r["assists"] or 0)) / max(1, deaths)
            data.append(
                ChampionAggregateResponse(
                    champion_id=r["champion_id"],
                    games_played=r["games_played"],
                    win_rate=float(r["win_rate"] or 0),
                    kda=round(float(kda), 2),
                    avg_kills=float(r["avg_kills"] or 0),
                    avg_deaths=float(r["avg_deaths"] or 0),
                    avg_assists=float(r["avg_assists"] or 0),
                    avg_gold=float(r["avg_gold"] or 0),
                )
            )
        return data
