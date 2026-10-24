# Sports Hub

Cricbuzz-style live scores, fixtures, standings and news for **cricket, football, hockey and kabaddi**.
Spark + Delta Lake for storage and jobs, FastAPI for the API.

```
Providers -> jobs/ingest_live (Spark) -> Delta tables <- app (FastAPI, delta-rs) -> mobile app
                                          matches / match_events / standings / news ...
```

The API reads Delta tables directly with delta-rs, so it needs no Spark cluster at request time.
Spark jobs write (DDL, MERGE upserts); the API picks up new commits within `DELTA_REFRESH_SECONDS`.

## Quick start

```bash
pip install -r requirements.txt
cp .env.example .env

# Option A: full lakehouse path (needs Java 17+)
python -m jobs.create_tables          # runs ddl/schema.sql on Spark + Delta
python -m jobs.seed                   # sample data via Spark MERGE
python -m jobs.simulate_live          # (second terminal) makes live scores move

# Option B: no Java, delta-rs only
python -m jobs.seed --engine delta-rs

uvicorn app.main:app --reload         # docs at http://localhost:8000/docs
pytest
```

## API (`/api/v1`)

| Endpoint | Purpose |
|---|---|
| `GET /sports` | The four sports |
| `GET /matches?sport_id=&status=live\|upcoming\|completed\|all` | Match lists |
| `GET /matches/live` | Live matches across all sports (home screen) |
| `GET /matches/{id}` | Scorecard summary plus events |
| `GET /matches/{id}/events?after_seq=N` | Incremental commentary |
| `GET /leagues`, `GET /leagues/{id}/standings` | Leagues and tables |
| `GET /teams/{id}` | Team and players |
| `GET /news?sport_id=` | News feed |
| `WS /ws/matches/{id}` | Snapshot, then pushes on score or new events |

## Design notes

- **One schema, four sports.** Sport-specific data sits in JSON columns (`score_json`, `payload_json`, `stats_json`).
  Cricket holds innings, football minutes and goals, hockey periods and clock, kabaddi halves and raid points.
  `app/scoring.py` renders the one-line summary per sport.
- **Delta features used:** partitioning by `sport_id`, CHECK constraints, change data feed and optimized writes on live tables.
  Delta has no primary or foreign keys, so uniqueness comes from MERGE keys (`jobs/seed_data.KEYS`).
- **Not in Delta:** user accounts, follows and device tokens are transactional. Put them in PostgreSQL.
- **Scaling the live path:** the WebSocket polls every 2s. For many concurrent users, publish updates from the
  ingest job to Redis pub/sub (or consume the Delta change data feed) and fan out from there.
- **Providers:** implement `ProviderAdapter` in `jobs/ingest_live.py`. `ExampleRestAdapter` uses placeholder field names.
- All sample names and scores are fictional.
