import datetime
from typing import Annotated

from sqlalchemy import Text, ForeignKey, Index, JSON
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship

intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
strpk = Annotated[str, mapped_column(primary_key=True)]
text = Annotated[str, mapped_column(Text)]


class Base(DeclarativeBase):
    pass

    def __repr__(self):
        cols = []
        for col in self.__table__.columns.keys():
            cols.append(f"{col}={getattr(self, col)!r}")
        return f"<{self.__class__.__name__}, {', '.join(cols)}>"


class Player(Base):
    __tablename__ = "players"

    puuid: Mapped[strpk]
    game_name: Mapped[text]
    tag_line: Mapped[text]
    updated_at: Mapped[datetime.datetime]

    __table_args__ = (Index("idx_game_name_tag_line", "game_name", "tag_line"),)

    match_stats: Mapped[list["MatchParticipant"]] = relationship(
        back_populates="player"
    )


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[intpk]
    puuid: Mapped[str] = mapped_column(ForeignKey("players.puuid"))
    tier: Mapped[text]
    rank: Mapped[text]
    league_points: Mapped[int]
    wins: Mapped[int]
    losses: Mapped[int]


class Match(Base):
    __tablename__ = "matches"

    match_id: Mapped[strpk]
    game_version: Mapped[text]
    game_creation: Mapped[datetime.datetime]
    game_duration: Mapped[datetime.timedelta]

    participants: Mapped[list["MatchParticipant"]] = relationship(
        back_populates="match"
    )


class MatchParticipant(Base):
    __tablename__ = "match_participants"

    id: Mapped[intpk]
    match_id: Mapped[str] = mapped_column(
        ForeignKey("matches.match_id", ondelete="CASCADE")
    )
    puuid: Mapped[str] = mapped_column(ForeignKey("players.puuid", ondelete="CASCADE"))
    champion_id: Mapped[int] = mapped_column(index=True)
    win: Mapped[bool]
    kills: Mapped[int]
    deaths: Mapped[int]
    assists: Mapped[int]
    team_position: Mapped[str]

    raw_data: Mapped[dict] = mapped_column(JSON)

    player: Mapped["Player"] = relationship(back_populates="match_stats")
    match: Mapped["Match"] = relationship(back_populates="participants")
