from __future__ import annotations

import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.models.base_models import League, Match, MatchParticipant, Player
from src.schemas.riot import RiotLeagueSchema, RiotMatchResponseSchema


class PlayerRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_riot_id(self, game_name: str, tag_line: str) -> Player | None:
        stmt = select(Player).where(
            Player.game_name == game_name, Player.tag_line == tag_line
        )
        return await self.session.scalar(stmt)

    async def get_profile(self, puuid: str) -> Player | None:
        stmt = (
            select(Player)
            .options(selectinload(Player.leagues))
            .where(Player.puuid == puuid)
        )
        return await self.session.scalar(stmt)

    async def upsert_player(self, puuid: str, game_name: str, tag_line: str) -> None:
        stmt = (
            insert(Player)
            .values(
                puuid=puuid,
                game_name=game_name,
                tag_line=tag_line,
                updated_at=datetime.datetime.now(datetime.timezone.utc),
            )
            .on_conflict_do_update(
                index_elements=[Player.puuid],
                set_={
                    "game_name": game_name,
                    "tag_line": tag_line,
                    "updated_at": datetime.datetime.now(datetime.timezone.utc),
                },
            )
        )
        await self.session.execute(stmt)

    async def replace_leagues(
        self, puuid: str, leagues: list[RiotLeagueSchema]
    ) -> None:
        await self.session.execute(delete(League).where(League.puuid == puuid))
        for league in leagues:
            self.session.add(League(puuid=puuid, **league.model_dump()))

    async def existing_match_ids(self, match_ids: list[str]) -> set[str]:
        if not match_ids:
            return set()
        rows = await self.session.scalars(
            select(Match.match_id).where(Match.match_id.in_(match_ids))
        )
        return set(rows.all())

    async def save_match(self, match: RiotMatchResponseSchema) -> None:
        info = match.info
        self.session.add(
            Match(
                match_id=match.match_id,
                game_version=info.game_version,
                game_creation=info.game_creation,
                game_start_timestamp=info.game_start_timestamp,
                game_end_timestamp=info.game_end_timestamp,
                game_duration=info.game_duration,
            )
        )
        for p in info.participants:
            self.session.add(
                MatchParticipant(
                    match_id=match.match_id,
                    raw_data=p.model_dump(mode="json", by_alias=True),
                    **p.model_dump(),
                )
            )

    async def recent_matches_for_player(
        self, puuid: str, limit: int = 20
    ) -> list[Match]:
        stmt = (
            select(Match)
            .join(MatchParticipant, MatchParticipant.match_id == Match.match_id)
            .where(MatchParticipant.puuid == puuid)
            .order_by(Match.game_start_timestamp.desc())
            .limit(limit)
            .options(selectinload(Match.participants))
        )
        rows = await self.session.scalars(stmt)
        return list(rows.unique().all())

    async def champion_aggregates(self, puuid: str) -> list[dict]:
        stmt = (
            select(
                MatchParticipant.champion_id,
                func.count(MatchParticipant.id).label("games_played"),
                (func.avg(func.cast(MatchParticipant.win, func.INTEGER)) * 100).label(
                    "win_rate"
                ),
                func.sum(MatchParticipant.kills).label("kills"),
                func.sum(MatchParticipant.deaths).label("deaths"),
                func.sum(MatchParticipant.assists).label("assists"),
                func.avg(MatchParticipant.kills).label("avg_kills"),
                func.avg(MatchParticipant.deaths).label("avg_deaths"),
                func.avg(MatchParticipant.assists).label("avg_assists"),
                func.avg(MatchParticipant.gold_earned).label("avg_gold"),
            )
            .where(MatchParticipant.puuid == puuid)
            .group_by(MatchParticipant.champion_id)
            .order_by(func.count(MatchParticipant.id).desc())
        )
        result = await self.session.execute(stmt)
        return [dict(r._mapping) for r in result]
