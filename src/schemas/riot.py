import datetime
from typing import Any

from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic.alias_generators import to_camel


class RiotBaseModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="ignore"
    )


class RiotAccountSchema(RiotBaseModel):
    """
    Reply from /riot/account/v1/accounts/by-riot-id/
    """

    puuid: str = Field(max_length=80)
    game_name: str
    tag_line: str


class RiotLeagueSchema(RiotBaseModel):
    """
    Array element from /lol/league/v4/entries/by-puuid/
    """

    queue_type: str = Field(max_length=30)
    tier: str = Field(max_length=20)
    rank: str = Field(max_length=10)
    league_points: int
    wins: int
    losses: int


class RiotParticipantSchema(RiotBaseModel):
    """
    Player object from info.participants array in Match-V5
    """

    champion_id: int

    # Financial metrics
    gold_earned: int
    gold_spent: int

    # Damage metrics
    total_damage_dealt: int
    total_damage_taken: int
    total_dd_to_champions: int = Field(alias="totalDamageDealtToChampions")

    # Combat metrics
    win: bool
    kills: int
    deaths: int
    assists: int
    team_position: str


class RiotMatchInfoSchema(RiotBaseModel):
    """
    info block inside Match-V5 response
    """

    game_version: str = Field(max_length=20)
    game_creation: datetime.datetime
    game_start_timestamp: datetime.datetime
    game_end_timestamp: datetime.datetime
    game_duration: int

    participants: list[RiotParticipantSchema]

    @field_validator("game_creation", "game_start_timestamp", "game_end_timestamp")
    @classmethod
    def parse_ms_timestamps(cls, v: Any) -> datetime.datetime:
        if isinstance(v, int):
            return datetime.datetime.fromtimestamp(v / 1000, tz=datetime.timezone.utc)
        return v


class RiotMatchResponseSchema(RiotBaseModel):
    """
    Top-level endpoint response /lol/match/v5/matches/{matchId}
    """
    metadata: dict[str, Any]
    info: RiotMatchInfoSchema

    @property
    def match_id(self) -> str:
        """
        Удобный хелпер, чтобы быстро доставать match_id из метаданных
        :return str
        """
        return self.metadata.get("matchId", "")
