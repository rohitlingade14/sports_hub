"""Turn sport-specific score documents into a one-line summary for list views."""


def score_summary(sport_id: str, score: dict | None) -> str:
    if not score:
        return ""
    if sport_id == "cricket":
        return " | ".join(f"{i['team_id'].upper()} {i['runs']}/{i['wickets']} ({i['overs']})"
                          for i in score.get("innings", []))
    if sport_id == "football":
        return f"{score['home']}-{score['away']} ({score.get('minute', 0)}')"
    if sport_id == "hockey":
        return f"{score['home']}-{score['away']} (Q{score.get('period', 1)} {score.get('clock', '')})".strip()
    if sport_id == "kabaddi":
        return f"{score['home']}-{score['away']} (H{score.get('half', 1)} {score.get('clock', '')})".strip()
    return ""
