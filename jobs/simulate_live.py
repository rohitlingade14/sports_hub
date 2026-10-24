"""Demo: advances the sample live matches so you can watch scores change in the API and WebSocket.
   python -m jobs.simulate_live --interval 3
"""
import argparse
import json
import random
import time
from datetime import datetime, timezone

# tick functions mutate `score` and return (event_type, description, team_ref) or None.
# team_ref is "home", "away" or an explicit team_id.


def tick_cricket(score: dict):
    inn = score["innings"][score["current_innings"] - 1]
    over, ball = map(int, inn["overs"].split("."))
    if over >= 20 or inn["wickets"] >= 10:
        return None
    ball += 1
    if ball == 6:
        over, ball = over + 1, 0
    inn["overs"] = f"{over}.{ball}"
    r = random.choices([0, 1, 2, 4, 6, "W"], [30, 30, 10, 15, 5, 10])[0]
    if r == "W":
        inn["wickets"] += 1
        return "wicket", f"Wicket! {inn['team_id'].upper()} {inn['runs']}/{inn['wickets']}", inn["team_id"]
    inn["runs"] += r
    if r in (4, 6):
        return "boundary", f"{'SIX' if r == 6 else 'FOUR'}! {inn['team_id'].upper()} {inn['runs']}/{inn['wickets']}", inn["team_id"]
    return None


def tick_football(score: dict):
    score["minute"] = min(90, score["minute"] + random.randint(1, 3))
    if random.random() < 0.12:
        side = random.choice(["home", "away"])
        score[side] += 1
        return "goal", f"Goal! {score['home']}-{score['away']}", side
    return None


def _countdown(score: dict, period_key: str, max_period: int, period_minutes: int) -> None:
    m, s = map(int, score["clock"].split(":"))
    total = m * 60 + s - random.randint(20, 60)
    if total <= 0:
        if score[period_key] < max_period:
            score[period_key] += 1
            total = period_minutes * 60
        else:
            total = 0
    score["clock"] = f"{total // 60:02d}:{total % 60:02d}"


def tick_hockey(score: dict):
    _countdown(score, "period", 4, 15)
    if random.random() < 0.10:
        side = random.choice(["home", "away"])
        score[side] += 1
        return "goal", f"Goal! {score['home']}-{score['away']}", side
    return None


def tick_kabaddi(score: dict):
    _countdown(score, "half", 2, 20)
    side = random.choice(["home", "away"])
    pts = random.choices([0, 1, 2, 3], [20, 50, 20, 10])[0]
    score[side] += pts
    if pts >= 2:
        return "super_raid", f"Super raid! +{pts} ({score['home']}-{score['away']})", side
    return None


TICKS = {"cricket": tick_cricket, "football": tick_football, "hockey": tick_hockey, "kabaddi": tick_kabaddi}


def clock_label(sport_id: str, score: dict) -> str:
    return {"cricket": lambda: score["innings"][score["current_innings"] - 1]["overs"],
            "football": lambda: f"{score['minute']}'",
            "hockey": lambda: f"Q{score['period']} {score['clock']}",
            "kabaddi": lambda: f"H{score['half']} {score['clock']}"}[sport_id]()


def main(interval: int) -> None:
    from pyspark.sql import functions as F

    from jobs.common import get_spark, table_path, upsert

    spark = get_spark("simulate-live")
    while True:
        now = datetime.now(timezone.utc)
        live = spark.read.format("delta").load(table_path("matches")).filter("status = 'live'").collect()
        matches, events = [], []
        for row in live:
            score = json.loads(row.score_json)
            result = TICKS[row.sport_id](score)
            m = row.asDict()
            m.update(score_json=json.dumps(score, separators=(",", ":")), updated_at=now)
            matches.append(m)
            if result:
                etype, desc, ref = result
                team = m[f"{ref}_team_id"] if ref in ("home", "away") else ref
                seq = (spark.read.format("delta").load(table_path("match_events"))
                       .filter(F.col("match_id") == row.match_id).agg(F.max("seq")).first()[0] or 0) + 1
                events.append(dict(event_id=f"{row.match_id}-e{seq}", match_id=row.match_id, sport_id=row.sport_id,
                                   seq=seq, clock=clock_label(row.sport_id, score), event_type=etype, team_id=team,
                                   player_id=None, description=desc, payload_json="{}", created_at=now))
        upsert(spark, "matches", matches, ["match_id"])
        upsert(spark, "match_events", events, ["event_id"])
        print(f"{now:%H:%M:%S} updated {len(matches)} matches, {len(events)} new events")
        time.sleep(interval)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=3)
    main(ap.parse_args().interval)
