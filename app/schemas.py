from datetime import datetime
from typing import Any

from pydantic import BaseModel


class Sport(BaseModel):
    sport_id: str
    name: str
    scoring_model: str


class League(BaseModel):
    league_id: str
    sport_id: str
    name: str
    country: str | None = None
    season: str | None = None


class TeamRef(BaseModel):
    team_id: str
    name: str
    short_name: str | None = None
    logo_url: str | None = None


class Player(BaseModel):
    player_id: str
    team_id: str
    sport_id: str
    name: str
    role: str | None = None
    meta: dict[str, Any] | None = None


class TeamDetail(TeamRef):
    sport_id: str
    country: str | None = None
    players: list[Player] = []


class Event(BaseModel):
    event_id: str
    match_id: str
    seq: int
    clock: str | None = None
    event_type: str
    team_id: str | None = None
    player_id: str | None = None
    description: str | None = None
    payload: dict[str, Any] | None = None
    created_at: datetime


class Match(BaseModel):
    match_id: str
    sport_id: str
    league_id: str | None = None
    status: str
    start_time: datetime
    venue: str | None = None
    home: TeamRef
    away: TeamRef
    score: dict[str, Any] | None = None
    score_summary: str = ""
    result_text: str | None = None
    updated_at: datetime


class MatchDetail(Match):
    events: list[Event] = []


class StandingRow(BaseModel):
    position: int
    team: TeamRef
    played: int | None = None
    won: int | None = None
    lost: int | None = None
    drawn: int | None = None
    points: int | None = None
    stats: dict[str, Any] | None = None


class NewsItem(BaseModel):
    news_id: str
    sport_id: str
    title: str
    summary: str | None = None
    source: str | None = None
    url: str | None = None
    published_at: datetime
