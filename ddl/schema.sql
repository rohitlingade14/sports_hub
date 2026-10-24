-- Sports Hub lakehouse DDL (Spark SQL + Delta Lake).
-- {base} is replaced with DELTA_BASE_PATH by jobs/create_tables.py.
-- Sport-specific data (innings, periods, raids) lives in *_json columns so one
-- schema serves cricket, football, hockey and kabaddi.

CREATE TABLE IF NOT EXISTS delta.`{base}/sports` (
  sport_id STRING NOT NULL COMMENT 'cricket, football, hockey, kabaddi',
  name STRING NOT NULL,
  scoring_model STRING NOT NULL COMMENT 'innings, goals, goals_periods, points_halves'
) USING DELTA;

CREATE TABLE IF NOT EXISTS delta.`{base}/leagues` (
  league_id STRING NOT NULL,
  sport_id STRING NOT NULL,
  name STRING NOT NULL,
  country STRING,
  season STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS delta.`{base}/teams` (
  team_id STRING NOT NULL,
  sport_id STRING NOT NULL,
  name STRING NOT NULL,
  short_name STRING,
  country STRING,
  logo_url STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS delta.`{base}/players` (
  player_id STRING NOT NULL,
  team_id STRING NOT NULL,
  sport_id STRING NOT NULL,
  name STRING NOT NULL,
  role STRING COMMENT 'batter, bowler, striker, goalkeeper, raider, defender',
  meta_json STRING
) USING DELTA;

CREATE TABLE IF NOT EXISTS delta.`{base}/matches` (
  match_id STRING NOT NULL,
  sport_id STRING NOT NULL,
  league_id STRING,
  home_team_id STRING NOT NULL,
  away_team_id STRING NOT NULL,
  start_time TIMESTAMP NOT NULL,
  status STRING NOT NULL COMMENT 'scheduled, live, completed, postponed, abandoned',
  venue STRING,
  score_json STRING COMMENT 'sport-specific live score document',
  result_text STRING,
  updated_at TIMESTAMP NOT NULL
) USING DELTA
PARTITIONED BY (sport_id)
TBLPROPERTIES (
  delta.enableChangeDataFeed = true,
  delta.autoOptimize.optimizeWrite = true
);

CREATE TABLE IF NOT EXISTS delta.`{base}/match_events` (
  event_id STRING NOT NULL,
  match_id STRING NOT NULL,
  sport_id STRING NOT NULL,
  seq BIGINT NOT NULL COMMENT 'monotonic per match, used for incremental fetch',
  clock STRING COMMENT 'over 14.2, minute 67, Q3 12:10, H2 06:30',
  event_type STRING NOT NULL COMMENT 'goal, wicket, boundary, super_raid, card, ...',
  team_id STRING,
  player_id STRING,
  description STRING,
  payload_json STRING,
  created_at TIMESTAMP NOT NULL
) USING DELTA
PARTITIONED BY (sport_id)
TBLPROPERTIES (
  delta.enableChangeDataFeed = true,
  delta.autoOptimize.optimizeWrite = true
);

CREATE TABLE IF NOT EXISTS delta.`{base}/standings` (
  league_id STRING NOT NULL,
  sport_id STRING NOT NULL,
  team_id STRING NOT NULL,
  position INT NOT NULL,
  played INT,
  won INT,
  lost INT,
  drawn INT,
  points INT,
  stats_json STRING COMMENT 'net run rate, goal difference, score difference, ...',
  updated_at TIMESTAMP NOT NULL
) USING DELTA;

CREATE TABLE IF NOT EXISTS delta.`{base}/news` (
  news_id STRING NOT NULL,
  sport_id STRING NOT NULL,
  title STRING NOT NULL,
  summary STRING,
  body STRING,
  source STRING,
  url STRING,
  published_at TIMESTAMP NOT NULL
) USING DELTA
PARTITIONED BY (sport_id);

-- Delta enforces CHECK constraints on every write (no primary or foreign keys in Delta).
ALTER TABLE delta.`{base}/matches` ADD CONSTRAINT valid_status CHECK (status IN ('scheduled','live','completed','postponed','abandoned'));
ALTER TABLE delta.`{base}/matches` ADD CONSTRAINT valid_sport CHECK (sport_id IN ('cricket','football','hockey','kabaddi'));
ALTER TABLE delta.`{base}/matches` ADD CONSTRAINT teams_differ CHECK (home_team_id <> away_team_id);
ALTER TABLE delta.`{base}/match_events` ADD CONSTRAINT valid_event_sport CHECK (sport_id IN ('cricket','football','hockey','kabaddi'));
