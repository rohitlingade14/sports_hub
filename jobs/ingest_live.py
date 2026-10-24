"""Provider ingestion: raw provider payloads -> canonical rows -> MERGE into Delta.

Add one adapter per provider/sport. The API and app never see provider formats.
   python -m jobs.ingest_live --interval 10
"""
import argparse
import json
import os
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import httpx

from jobs.common import get_spark, upsert


class ProviderAdapter(ABC):
    sport_id: str

    @abstractmethod
    def fetch_live(self) -> list[dict]:
        """Return raw provider payloads for matches in progress."""

    @abstractmethod
    def to_match_row(self, raw: dict) -> dict:
        """Map one raw payload to a `matches` row."""

    def to_event_rows(self, raw: dict, match_id: str) -> list[dict]:
        return []


class ExampleRestAdapter(ProviderAdapter):
    """Template for a REST provider. Field names below are placeholders: map them to your provider's schema."""

    def __init__(self, sport_id: str, base_url: str, api_key: str):
        self.sport_id, self.base_url, self.api_key = sport_id, base_url, api_key

    def fetch_live(self) -> list[dict]:
        r = httpx.get(f"{self.base_url}/live", params={"sport": self.sport_id},
                      headers={"Authorization": f"Bearer {self.api_key}"}, timeout=10)
        r.raise_for_status()
        return r.json()["matches"]

    def to_match_row(self, raw: dict) -> dict:
        return dict(
            match_id=f"{self.sport_id}-{raw['id']}", sport_id=self.sport_id, league_id=raw.get("league_id"),
            home_team_id=raw["home"]["id"], away_team_id=raw["away"]["id"],
            start_time=datetime.fromisoformat(raw["start"]), status="live" if raw["in_play"] else raw["status"],
            venue=raw.get("venue"), score_json=json.dumps(raw["score"], separators=(",", ":")),
            result_text=raw.get("result"), updated_at=datetime.now(timezone.utc),
        )

    def to_event_rows(self, raw: dict, match_id: str) -> list[dict]:
        return [dict(event_id=f"{match_id}-e{ev['seq']}", match_id=match_id, sport_id=self.sport_id, seq=ev["seq"],
                     clock=ev.get("clock"), event_type=ev["type"], team_id=ev.get("team_id"),
                     player_id=ev.get("player_id"), description=ev.get("text"), payload_json=json.dumps(ev),
                     created_at=datetime.now(timezone.utc)) for ev in raw.get("events", [])]


def run_once(spark, adapters: list[ProviderAdapter]) -> None:
    for a in adapters:
        raws = a.fetch_live()
        matches = [a.to_match_row(r) for r in raws]
        events = [e for r, m in zip(raws, matches) for e in a.to_event_rows(r, m["match_id"])]
        upsert(spark, "matches", matches, ["match_id"])
        upsert(spark, "match_events", events, ["event_id"])
        print(f"[{a.sport_id}] merged {len(matches)} matches, {len(events)} events")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=0, help="seconds between polls (0 = once)")
    args = ap.parse_args()
    key = os.environ["PROVIDER_API_KEY"]
    url = os.environ["PROVIDER_BASE_URL"]
    adapters = [ExampleRestAdapter(s, url, key) for s in ("cricket", "football", "hockey", "kabaddi")]
    spark = get_spark("ingest-live")
    while True:
        run_once(spark, adapters)
        if not args.interval:
            break
        time.sleep(args.interval)
