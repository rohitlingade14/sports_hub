def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_sports(client):
    ids = {x["sport_id"] for x in client.get("/api/v1/sports").json()}
    assert ids == {"cricket", "football", "hockey", "kabaddi"}


def test_live_matches_cover_all_sports(client):
    live = client.get("/api/v1/matches/live").json()
    assert {m["sport_id"] for m in live} == {"cricket", "football", "hockey", "kabaddi"}
    assert all(m["status"] == "live" and m["score_summary"] for m in live)


def test_filter_by_sport_and_status(client):
    up = client.get("/api/v1/matches", params={"sport_id": "hockey", "status": "upcoming"}).json()
    assert [m["match_id"] for m in up] == ["hoc-002"]
    assert client.get("/api/v1/matches", params={"sport_id": "rugby"}).status_code == 404


def test_match_detail_and_incremental_events(client):
    d = client.get("/api/v1/matches/cri-001").json()
    assert d["home"]["name"] == "Mumbai Indians" and len(d["events"]) == 3
    later = client.get("/api/v1/matches/cri-001/events", params={"after_seq": 2}).json()
    assert [e["seq"] for e in later] == [3]
    assert client.get("/api/v1/matches/nope").status_code == 404


def test_standings_team_news(client):
    st = client.get("/api/v1/leagues/ipl/standings").json()
    assert [r["position"] for r in st] == [1, 2, 3, 4]
    assert client.get("/api/v1/teams/mi").json()["players"][0]["name"] == "A. Verma"
    assert all(n["sport_id"] == "kabaddi" for n in client.get("/api/v1/news", params={"sport_id": "kabaddi"}).json())


def test_websocket_snapshot(client):
    with client.websocket_connect("/api/v1/ws/matches/foo-001") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "snapshot" and msg["match"]["match_id"] == "foo-001"


def test_simulator_ticks_keep_scores_valid():
    import json
    import random

    from jobs.seed_data import build_matches
    from jobs.simulate_live import TICKS, clock_label
    from datetime import datetime, timezone

    random.seed(7)
    for m in (x for x in build_matches(datetime.now(timezone.utc)) if x["status"] == "live"):
        score = json.loads(m["score_json"])
        for _ in range(200):
            TICKS[m["sport_id"]](score)
        assert clock_label(m["sport_id"], score)
