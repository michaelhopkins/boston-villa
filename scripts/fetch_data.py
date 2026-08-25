#!/usr/bin/env python3
"""Pull Boston Villa's fixtures and division standings into data.json.

Run by .github/workflows/refresh.yml once an hour. Writes data.json only when
the football has actually changed, so the repo doesn't collect an empty commit
every hour and the "last changed" stamp on the page stays truthful.

Venue corrections are NOT handled here — those live in the OVERRIDES block in
index.html and are applied in the browser, so a refresh can never clobber them.
"""

import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "https://reg.mass-soccer.org/api"
CONTEXT = {"league_id": 7, "season_id": 179, "bracket_id": 60, "division_id": 152}
TEAM_ID = 30071          # Boston Villa FC's seasonlineup id
US = "Boston Villa FC"
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data.json")

# Identify ourselves so the league can see who's calling and get in touch.
UA = "boston-villa-page/1.0 (+https://github.com/michaelhopkins/boston-villa)"

SURFACE = {"T": "Turf", "G": "Grass"}


def get(path, **extra):
    url = f"{BASE}/{path}/?" + urllib.parse.urlencode({**CONTEXT, **extra})
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def num(value):
    """Coordinates arrive as strings, and occasionally not at all."""
    try:
        return round(float(value), 6)
    except (TypeError, ValueError):
        return None


def build_games(raw):
    games = []
    for g in raw:
        home = g.get("home_seasonlineup_id") == TEAM_ID
        games.append({
            "date": g.get("game_date"),
            "iso": g.get("game_datetime"),          # the only trustworthy kick-off field
            "home": home,
            "opp": (g.get("away_team_name") if home else g.get("home_team_name")) or "",
            "venue": (g.get("field_name") or "").strip(),
            "surface": SURFACE.get(g.get("field_surface"), "Unknown"),
            "addr": (g.get("field_address") or "").strip(),
            "city": (g.get("field_address_city") or "").strip(),
            "lat": num(g.get("field_address_latitude")),
            "lng": num(g.get("field_address_longitude")),
            # Carried for future use; the page doesn't render results yet.
            "us": g.get("home_team_score") if home else g.get("away_team_score"),
            "them": g.get("away_team_score") if home else g.get("home_team_score"),
            "final": bool(g.get("score_is_official")),
            "postponed": bool(g.get("postponed")),
        })
    return sorted(games, key=lambda g: g["iso"] or "")


def build_table(raw):
    """League order as the feed gives it; the page re-sorts once games are played."""
    return [{
        "id": r.get("team_id"),
        "club": r.get("team_name") or "",
        "gp": r.get("games_played") or 0,
        "w": r.get("wins") or 0,
        "d": r.get("ties") or 0,
        "l": r.get("losses") or 0,
        "gf": r.get("goals_for") or 0,
        "ga": r.get("goals_against") or 0,
        "pts": r.get("points") or 0,
    } for r in sorted(raw, key=lambda r: r.get("place") or 0)]


def main():
    try:
        raw_games = get("games", team_id=TEAM_ID, fa=1)
        raw_table = get("standings")
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        # A blip on their end is not a reason to fail the run or blank the page.
        print(f"league API unreachable: {exc}", file=sys.stderr)
        return 0

    games = build_games(raw_games)
    table = build_table(raw_table)

    if not games or not table:
        print("league API returned an empty schedule or table; leaving data.json alone",
              file=sys.stderr)
        return 0

    payload = {"games": games, "table": table}

    # Compare the football only — ignore the timestamp — so an unchanged week
    # produces no commit at all.
    try:
        with open(OUT) as fh:
            existing = json.load(fh)
        if {k: existing.get(k) for k in ("games", "table")} == payload:
            print("no change")
            return 0
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    payload["updated"] = datetime.now(timezone.utc).strftime("%d %B %Y")
    with open(OUT, "w") as fh:
        json.dump(payload, fh, indent=1, ensure_ascii=False)
        fh.write("\n")
    print(f"updated: {len(games)} games, {len(table)} clubs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
