"""Sample data for cricket, football, hockey and kabaddi. All names and scores are fictional sample data."""
import json
from datetime import datetime, timedelta, timezone


def _j(o) -> str:
    return json.dumps(o, separators=(",", ":"))


SPORTS = [
    dict(sport_id="cricket", name="Cricket", scoring_model="innings"),
    dict(sport_id="football", name="Football", scoring_model="goals"),
    dict(sport_id="hockey", name="Hockey", scoring_model="goals_periods"),
    dict(sport_id="kabaddi", name="Kabaddi", scoring_model="points_halves"),
]

LEAGUES = [
    dict(league_id="ipl", sport_id="cricket", name="Indian Premier League", country="IN", season="2026"),
    dict(league_id="isl", sport_id="football", name="Indian Super League", country="IN", season="2026-27"),
    dict(league_id="hil", sport_id="hockey", name="Hockey India League", country="IN", season="2026-27"),
    dict(league_id="pkl", sport_id="kabaddi", name="Pro Kabaddi League", country="IN", season="2026"),
]

_TEAMS = {
    "cricket": [("mi", "Mumbai Indians", "MI"), ("csk", "Chennai Super Kings", "CSK"),
                ("rcb", "Royal Challengers Bengaluru", "RCB"), ("kkr", "Kolkata Knight Riders", "KKR")],
    "football": [("mcfc", "Mumbai City FC", "MCFC"), ("bfc", "Bengaluru FC", "BFC"),
                 ("kbfc", "Kerala Blasters FC", "KBFC"), ("fcg", "FC Goa", "FCG")],
    "hockey": [("dsp", "Delhi SG Pipers", "DSP"), ("shc", "Soorma Hockey Club", "SHC"),
               ("tnd", "Tamil Nadu Dragons", "TND"), ("kl", "Kalinga Lancers", "KL")],
    "kabaddi": [("pp", "Patna Pirates", "PP"), ("jpp", "Jaipur Pink Panthers", "JPP"),
                ("um", "U Mumba", "UM"), ("bb", "Bengaluru Bulls", "BB")],
}
_LEAGUE_OF = {"cricket": "ipl", "football": "isl", "hockey": "hil", "kabaddi": "pkl"}

TEAMS = [
    dict(team_id=tid, sport_id=sport, name=name, short_name=short, country="IN",
         logo_url=f"https://cdn.example.com/logos/{tid}.png")
    for sport, teams in _TEAMS.items() for tid, name, short in teams
]

PLAYERS = [
    dict(player_id="p-mi-1", team_id="mi", sport_id="cricket", name="A. Verma", role="batter", meta_json=_j({"jersey": 18})),
    dict(player_id="p-csk-1", team_id="csk", sport_id="cricket", name="R. Nair", role="bowler", meta_json=_j({"jersey": 7})),
    dict(player_id="p-mcfc-1", team_id="mcfc", sport_id="football", name="S. Thapa", role="striker", meta_json=_j({"jersey": 9})),
    dict(player_id="p-bfc-1", team_id="bfc", sport_id="football", name="K. Singh", role="goalkeeper", meta_json=_j({"jersey": 1})),
    dict(player_id="p-dsp-1", team_id="dsp", sport_id="hockey", name="H. Bedi", role="forward", meta_json=_j({"jersey": 11})),
    dict(player_id="p-shc-1", team_id="shc", sport_id="hockey", name="M. Rao", role="defender", meta_json=_j({"jersey": 5})),
    dict(player_id="p-pp-1", team_id="pp", sport_id="kabaddi", name="V. Kumar", role="raider", meta_json=_j({"jersey": 3})),
    dict(player_id="p-um-1", team_id="um", sport_id="kabaddi", name="D. Patil", role="defender", meta_json=_j({"jersey": 8})),
]


def build_matches(now: datetime) -> list[dict]:
    def m(mid, sport, h, a, hours, status, venue, score=None, result=None):
        return dict(match_id=mid, sport_id=sport, league_id=_LEAGUE_OF[sport], home_team_id=h, away_team_id=a,
                    start_time=now + timedelta(hours=hours), status=status, venue=venue,
                    score_json=_j(score) if score else None, result_text=result, updated_at=now)

    return [
        # cricket
        m("cri-001", "cricket", "mi", "csk", -2, "live", "Wankhede Stadium, Mumbai",
          {"innings": [{"team_id": "mi", "runs": 182, "wickets": 5, "overs": "20.0"},
                       {"team_id": "csk", "runs": 121, "wickets": 3, "overs": "14.2"}],
           "current_innings": 2, "target": 183}),
        m("cri-002", "cricket", "rcb", "kkr", 24, "scheduled", "M. Chinnaswamy Stadium, Bengaluru"),
        m("cri-003", "cricket", "csk", "rcb", -26, "completed", "MA Chidambaram Stadium, Chennai",
          {"innings": [{"team_id": "csk", "runs": 168, "wickets": 8, "overs": "20.0"},
                       {"team_id": "rcb", "runs": 169, "wickets": 4, "overs": "18.3"}],
           "current_innings": 2, "target": 169}, "RCB won by 6 wickets"),
        # football
        m("foo-001", "football", "mcfc", "bfc", -1, "live", "Mumbai Football Arena",
          {"home": 1, "away": 1, "minute": 67}),
        m("foo-002", "football", "kbfc", "fcg", 30, "scheduled", "Jawaharlal Nehru Stadium, Kochi"),
        m("foo-003", "football", "fcg", "mcfc", -50, "completed", "Fatorda Stadium, Goa",
          {"home": 0, "away": 2, "minute": 90}, "Mumbai City FC won 2-0"),
        # hockey
        m("hoc-001", "hockey", "dsp", "shc", -1, "live", "Major Dhyan Chand Stadium, Delhi",
          {"home": 3, "away": 2, "period": 3, "clock": "08:12"}),
        m("hoc-002", "hockey", "tnd", "kl", 20, "scheduled", "Mayor Radhakrishnan Stadium, Chennai"),
        m("hoc-003", "hockey", "kl", "dsp", -30, "completed", "Kalinga Stadium, Bhubaneswar",
          {"home": 2, "away": 2, "period": 4, "clock": "00:00"}, "Match drawn 2-2"),
        # kabaddi
        m("kab-001", "kabaddi", "pp", "um", -1, "live", "Patliputra Sports Complex, Patna",
          {"home": 28, "away": 24, "half": 2, "clock": "06:30"}),
        m("kab-002", "kabaddi", "jpp", "bb", 26, "scheduled", "SMS Indoor Stadium, Jaipur"),
        m("kab-003", "kabaddi", "bb", "pp", -28, "completed", "Kanteerava Indoor Stadium, Bengaluru",
          {"home": 35, "away": 38, "half": 2, "clock": "00:00"}, "Patna Pirates won by 3 points"),
    ]


def build_events(now: datetime) -> list[dict]:
    def e(mid, sport, seq, clock, etype, team, player, desc, mins_ago):
        return dict(event_id=f"{mid}-e{seq}", match_id=mid, sport_id=sport, seq=seq, clock=clock,
                    event_type=etype, team_id=team, player_id=player, description=desc,
                    payload_json=_j({}), created_at=now - timedelta(minutes=mins_ago))

    return [
        e("cri-001", "cricket", 1, "3.4", "boundary", "mi", "p-mi-1", "SIX! A. Verma clears long-on", 110),
        e("cri-001", "cricket", 2, "9.1", "wicket", "mi", None, "Wicket! MI lose their third", 90),
        e("cri-001", "cricket", 3, "11.5", "wicket", "csk", "p-csk-1", "Wicket! R. Nair strikes", 25),
        e("foo-001", "football", 1, "23'", "goal", "mcfc", "p-mcfc-1", "Goal! S. Thapa finishes from close range", 45),
        e("foo-001", "football", 2, "52'", "goal", "bfc", None, "Goal! Bengaluru FC level from a corner", 20),
        e("hoc-001", "hockey", 1, "Q1 09:40", "goal", "dsp", "p-dsp-1", "Goal! H. Bedi from a penalty corner", 70),
        e("hoc-001", "hockey", 2, "Q2 04:10", "goal", "shc", None, "Goal! Soorma equalise", 50),
        e("kab-001", "kabaddi", 1, "H1 12:05", "super_raid", "pp", "p-pp-1", "Super raid! V. Kumar picks up 3 points", 60),
        e("kab-001", "kabaddi", 2, "H2 10:20", "super_raid", "um", None, "Super raid! U Mumba take 2", 15),
    ]


def build_standings(now: datetime) -> list[dict]:
    rows = []
    layout = {
        "ipl": [("rcb", 6, 5, 1, 0, 10, {"nrr": 0.82}), ("mi", 6, 4, 2, 0, 8, {"nrr": 0.41}),
                ("csk", 6, 3, 3, 0, 6, {"nrr": -0.05}), ("kkr", 6, 1, 5, 0, 2, {"nrr": -1.12})],
        "isl": [("mcfc", 5, 4, 0, 1, 13, {"gd": 7}), ("bfc", 5, 3, 1, 1, 10, {"gd": 3}),
                ("fcg", 5, 1, 3, 1, 4, {"gd": -2}), ("kbfc", 5, 0, 4, 1, 1, {"gd": -8})],
        "hil": [("dsp", 5, 4, 0, 1, 13, {"gd": 9}), ("kl", 5, 3, 1, 1, 10, {"gd": 4}),
                ("shc", 5, 1, 3, 1, 4, {"gd": -3}), ("tnd", 5, 0, 4, 1, 1, {"gd": -10})],
        "pkl": [("pp", 8, 6, 2, 0, 33, {"score_diff": 41}), ("um", 8, 5, 3, 0, 28, {"score_diff": 20}),
                ("jpp", 8, 3, 5, 0, 18, {"score_diff": -9}), ("bb", 8, 2, 6, 0, 12, {"score_diff": -52})],
    }
    sport_of = {v: k for k, v in _LEAGUE_OF.items()}
    for league_id, table in layout.items():
        for pos, (tid, p, w, l, d, pts, stats) in enumerate(table, start=1):
            rows.append(dict(league_id=league_id, sport_id=sport_of[league_id], team_id=tid, position=pos,
                             played=p, won=w, lost=l, drawn=d, points=pts, stats_json=_j(stats), updated_at=now))
    return rows


def build_news(now: datetime) -> list[dict]:
    items = [
        ("cricket", "Chase on as CSK close in on 183", "CSK need 62 from 34 balls with seven wickets in hand."),
        ("cricket", "RCB top the table after fifth win", "Bengaluru lead the IPL standings on net run rate."),
        ("football", "Thapa strike keeps Mumbai City in the hunt", "Mumbai City FC and Bengaluru FC are level in the second half."),
        ("football", "Kochi braces for Goa visit", "Kerala Blasters host FC Goa tomorrow night."),
        ("hockey", "Pipers lead as Q3 enters final minutes", "Delhi SG Pipers hold a one-goal lead over Soorma."),
        ("hockey", "Lancers settle for a draw in Bhubaneswar", "Kalinga and Delhi shared the points in a 2-2 thriller."),
        ("kabaddi", "Patna take control in second half", "Pirates lead U Mumba 28-24 with six minutes left."),
        ("kabaddi", "Bulls fall short by three points", "Patna edged Bengaluru in a tight contest."),
    ]
    return [dict(news_id=f"n-{i}", sport_id=s, title=t, summary=sm, body=sm, source="Sports Hub Desk",
                 url=f"https://example.com/news/{i}", published_at=now - timedelta(minutes=15 * i))
            for i, (s, t, sm) in enumerate(items, start=1)]


KEYS = {
    "sports": ["sport_id"], "leagues": ["league_id"], "teams": ["team_id"], "players": ["player_id"],
    "matches": ["match_id"], "match_events": ["event_id"], "standings": ["league_id", "team_id"],
    "news": ["news_id"],
}
PARTITIONS = {"matches": ["sport_id"], "match_events": ["sport_id"], "news": ["sport_id"]}


def build_all(now: datetime | None = None) -> dict[str, list[dict]]:
    now = (now or datetime.now(timezone.utc)).replace(microsecond=0)
    return {
        "sports": SPORTS, "leagues": LEAGUES, "teams": TEAMS, "players": PLAYERS,
        "matches": build_matches(now), "match_events": build_events(now),
        "standings": build_standings(now), "news": build_news(now),
    }
