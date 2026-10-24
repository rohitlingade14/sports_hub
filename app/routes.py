import asyncio
import json
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect

from app import schemas as s
from app.scoring import score_summary
from app.store import DeltaStore, get_store

router = APIRouter()

SPORT_IDS = ("cricket", "football", "hockey", "kabaddi")
StatusFilter = Literal["live", "upcoming", "completed", "all"]
STATUS_MAP = {"live": ["live"], "upcoming": ["scheduled"], "completed": ["completed"]}


def _loads(v: str | None):
    return json.loads(v) if v else None


def _teams(store: DeltaStore) -> dict[str, dict]:
    return {t["team_id"]: t for t in store.read("teams")}


def _ref(teams: dict, tid: str) -> s.TeamRef:
    t = teams.get(tid, {})
    return s.TeamRef(team_id=tid, name=t.get("name", tid), short_name=t.get("short_name"), logo_url=t.get("logo_url"))


def _match(row: dict, teams: dict) -> s.Match:
    score = _loads(row.get("score_json"))
    return s.Match(
        match_id=row["match_id"], sport_id=row["sport_id"], league_id=row.get("league_id"), status=row["status"],
        start_time=row["start_time"], venue=row.get("venue"), home=_ref(teams, row["home_team_id"]),
        away=_ref(teams, row["away_team_id"]), score=score, score_summary=score_summary(row["sport_id"], score),
        result_text=row.get("result_text"), updated_at=row["updated_at"],
    )


def _event(row: dict) -> s.Event:
    return s.Event(**{k: row.get(k) for k in ("event_id", "match_id", "seq", "clock", "event_type", "team_id",
                                               "player_id", "description", "created_at")},
                   payload=_loads(row.get("payload_json")))


def _check_sport(sport_id: str) -> None:
    if sport_id not in SPORT_IDS:
        raise HTTPException(404, f"Unknown sport '{sport_id}'")


def _list_matches(store: DeltaStore, sport_id: str | None, status: StatusFilter, limit: int) -> list[s.Match]:
    filters: list[tuple] = []
    if sport_id:
        filters.append(("sport_id", "=", sport_id))
    if status != "all":
        filters.append(("status", "in", STATUS_MAP[status]))
    rows = store.read("matches", filters or None)
    rows.sort(key=lambda r: r["start_time"], reverse=(status == "completed"))
    teams = _teams(store)
    return [_match(r, teams) for r in rows[:limit]]


@router.get("/sports", response_model=list[s.Sport])
def list_sports(store: DeltaStore = Depends(get_store)):
    return store.read("sports")


@router.get("/matches", response_model=list[s.Match])
def list_matches(sport_id: str | None = None, status: StatusFilter = "all", limit: int = Query(50, le=200),
                 store: DeltaStore = Depends(get_store)):
    if sport_id:
        _check_sport(sport_id)
    return _list_matches(store, sport_id, status, limit)


@router.get("/matches/live", response_model=list[s.Match])
def live_matches(store: DeltaStore = Depends(get_store)):
    return _list_matches(store, None, "live", 100)


def _detail(store: DeltaStore, match_id: str, after_seq: int = 0) -> s.MatchDetail:
    rows = store.read("matches", [("match_id", "=", match_id)])
    if not rows:
        raise HTTPException(404, "Match not found")
    events = [e for e in store.read("match_events", [("match_id", "=", match_id)]) if e["seq"] > after_seq]
    events.sort(key=lambda e: e["seq"])
    base = _match(rows[0], _teams(store))
    return s.MatchDetail(**base.model_dump(), events=[_event(e) for e in events])


@router.get("/matches/{match_id}", response_model=s.MatchDetail)
def match_detail(match_id: str, store: DeltaStore = Depends(get_store)):
    return _detail(store, match_id)


@router.get("/matches/{match_id}/events", response_model=list[s.Event])
def match_events(match_id: str, after_seq: int = 0, store: DeltaStore = Depends(get_store)):
    return _detail(store, match_id, after_seq).events


@router.get("/leagues", response_model=list[s.League])
def list_leagues(sport_id: str | None = None, store: DeltaStore = Depends(get_store)):
    if sport_id:
        _check_sport(sport_id)
    return store.read("leagues", [("sport_id", "=", sport_id)] if sport_id else None)


@router.get("/leagues/{league_id}/standings", response_model=list[s.StandingRow])
def standings(league_id: str, store: DeltaStore = Depends(get_store)):
    rows = store.read("standings", [("league_id", "=", league_id)])
    if not rows:
        raise HTTPException(404, "No standings for this league")
    teams = _teams(store)
    rows.sort(key=lambda r: r["position"])
    return [s.StandingRow(position=r["position"], team=_ref(teams, r["team_id"]), played=r.get("played"),
                          won=r.get("won"), lost=r.get("lost"), drawn=r.get("drawn"), points=r.get("points"),
                          stats=_loads(r.get("stats_json"))) for r in rows]


@router.get("/teams/{team_id}", response_model=s.TeamDetail)
def team_detail(team_id: str, store: DeltaStore = Depends(get_store)):
    rows = store.read("teams", [("team_id", "=", team_id)])
    if not rows:
        raise HTTPException(404, "Team not found")
    t = rows[0]
    players = [s.Player(**{k: p.get(k) for k in ("player_id", "team_id", "sport_id", "name", "role")},
                        meta=_loads(p.get("meta_json")))
               for p in store.read("players", [("team_id", "=", team_id)])]
    return s.TeamDetail(team_id=team_id, name=t["name"], short_name=t.get("short_name"), logo_url=t.get("logo_url"),
                        sport_id=t["sport_id"], country=t.get("country"), players=players)


@router.get("/news", response_model=list[s.NewsItem])
def news(sport_id: str | None = None, limit: int = Query(20, le=100), store: DeltaStore = Depends(get_store)):
    if sport_id:
        _check_sport(sport_id)
    rows = store.read("news", [("sport_id", "=", sport_id)] if sport_id else None)
    rows.sort(key=lambda r: r["published_at"], reverse=True)
    return rows[:limit]


@router.websocket("/ws/matches/{match_id}")
async def match_socket(ws: WebSocket, match_id: str, store: DeltaStore = Depends(get_store)):
    """Pushes the match snapshot, then only changes (score or new events). Poll-based for the MVP;
    swap for Redis pub/sub or Delta change data feed when you scale out."""
    await ws.accept()
    last_updated, last_seq = None, 0
    try:
        while True:
            try:
                detail = await asyncio.to_thread(_detail, store, match_id, last_seq)
            except HTTPException:
                await ws.send_json({"type": "error", "detail": "Match not found"})
                break
            if last_updated is None or detail.updated_at != last_updated or detail.events:
                kind = "snapshot" if last_updated is None else "update"
                await ws.send_text(json.dumps({"type": kind, "match": json.loads(detail.model_dump_json())}))
                last_updated = detail.updated_at
                last_seq = max([last_seq] + [e.seq for e in detail.events])
            await asyncio.sleep(2)
    except WebSocketDisconnect:
        pass
