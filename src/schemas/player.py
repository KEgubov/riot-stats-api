import datetime
from pydantic import BaseModel, ConfigDict, Field


class BaseAPIModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LeagueResponse(BaseAPIModel):
    """
    Player league statistics
    """
    id: int
    queue_type: str = Field(description="Queue type (for example, RANKED_SOLO_5x5)")
    tier: str = Field(description="Tier (GOLD, DIAMOND, etc.)")
    rank: str = Field(description="Rank (I, II, III, IV)")
    league_points: int = Field(description="League Points (LP)")
    wins: int
    losses: int

class PlayerProfileResponse(BaseAPIModel):
    """
    Player Profile
    """
    puuid: str
    game_name: str
    tag_line: str
    updated_at: datetime.datetime
    leagues: list[LeagueResponse] = Field(default_factory=list)


class MatchParticipantResponse(BaseAPIModel):
    """
    Details of a specific participant in the match history display
    """

    id: int
    match_id: str
    puuid: str
    champion_id: int

    # Financial metrics
    gold_earned: int
    gold_spent: int

    # Combat metrics
    win: bool
    kills: int
    deaths: int
    assists: int
    team_position: str

    # Damage metrics
    total_damage_dealt: int = Field(description="Total damage dealt")
    total_damage_taken: int = Field(description="Total damage taken")
    total_dd_to_champions: int = Field(description="Total damage dealt to champions")


class MatchResponse(BaseAPIModel):
    """
    Basic information about the match
    """

    match_id: str
    game_version: str
    game_creation: datetime.datetime
    game_start_timestamp: datetime.datetime
    game_end_timestamp: datetime.datetime
    game_duration: int

    participants: list[MatchParticipantResponse]


class ChampionAggregateResponse(BaseAPIModel):
    """
    Aggregated player statistics for a specific champion
    """

    champion_id: int = Field(description="Champion ID")
    games_played: int = Field(..., description="Total games played")
    win_rate: float = Field(description="Win percentage (from 0.0 to 100.0)")
    kda: float = Field(description="KDA Rate ((Kills + Assists) Deaths)")

    # Averages per game
    avg_kills: float
    avg_deaths: float
    avg_assists: float
    avg_gold: float
