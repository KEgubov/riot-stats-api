import datetime
from typing import Annotated

from sqlalchemy import Text, ForeignKey, Index, String, DateTime
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, relationship

str_10 = Annotated[str, 10]
str_20 = Annotated[str, 20]
str_30 = Annotated[str, 30]
str_40 = Annotated[str, 40]
str_80 = Annotated[str, 80]
str_100 = Annotated[str, 100]

intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
strpk = Annotated[str_80, mapped_column(primary_key=True)]
text = Annotated[str, mapped_column(Text)]


class Base(DeclarativeBase):
    type_annotation_map = {
        str_20: String(20),
        str_30: String(30),
        str_40: String(40),
        str_80: String(80),
        str_100: String(100),
    }

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
    updated_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))

    __table_args__ = (Index("idx_game_name_tag_line", "game_name", "tag_line"),)

    match_stats: Mapped[list["MatchParticipant"]] = relationship(
        back_populates="player"
    )


class League(Base):
    __tablename__ = "leagues"

    id: Mapped[intpk]
    puuid: Mapped[str_80] = mapped_column(
        ForeignKey("players.puuid", ondelete="CASCADE")
    )
    queue_type: Mapped[str_30]
    tier: Mapped[str_20]
    rank: Mapped[str_10]
    league_points: Mapped[int]
    wins: Mapped[int]
    losses: Mapped[int]


class Match(Base):
    __tablename__ = "matches"

    match_id: Mapped[str_40] = mapped_column(primary_key=True)
    game_version: Mapped[str_20]
    game_creation: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True))
    game_duration: Mapped[int]

    participants: Mapped[list["MatchParticipant"]] = relationship(
        back_populates="match"
    )


class MatchParticipant(Base):
    __tablename__ = "match_participants"

    id: Mapped[intpk]
    match_id: Mapped[str_40] = mapped_column(
        ForeignKey("matches.match_id", ondelete="CASCADE"), index=True
    )
    puuid: Mapped[str_80] = mapped_column(
        ForeignKey("players.puuid", ondelete="CASCADE"), index=True
    )
    champion_id: Mapped[int] = mapped_column(index=True)
    win: Mapped[bool]
    kills: Mapped[int]
    deaths: Mapped[int]
    assists: Mapped[int]
    team_position: Mapped[str_20]

    raw_data: Mapped[dict] = mapped_column(JSONB)

    player: Mapped["Player"] = relationship(back_populates="match_stats")
    match: Mapped["Match"] = relationship(back_populates="participants")
