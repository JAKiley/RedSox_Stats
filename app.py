# app.py
from datetime import date, timedelta

from flask import Flask, jsonify, request, send_from_directory
import requests
import statsapi
from werkzeug.exceptions import HTTPException

app = Flask(__name__, static_folder="static", static_url_path="/static")

RED_SOX_ID = 111
AMERICAN_LEAGUE_ID = 103
AL_EAST_ID = 201

# Team leader categories shown on the page: (API category, stat group, label).
# The same category can come back for several groups (homeRuns is also
# "home runs allowed" for pitchers), so each one is tied to a group.
LEADER_CATEGORIES = [
    ("battingAverage", "hitting", "Batting Average"),
    ("homeRuns", "hitting", "Home Runs"),
    ("runsBattedIn", "hitting", "RBI"),
    ("earnedRunAverage", "pitching", "ERA"),
    ("wins", "pitching", "Wins"),
    ("strikeouts", "pitching", "Strikeouts (Pitching)"),
    ("saves", "pitching", "Saves"),
]
LEADER_LIMIT = 3


def player_url(full_name: str, player_id: int) -> str:
    """Build a player's mlb.com page link, e.g. https://www.mlb.com/player/rafael-devers-646240"""
    name_slug = full_name.lower().replace(" ", "-")
    return f"https://www.mlb.com/player/{name_slug}-{player_id}"


def game_to_json(game_pk: int) -> dict:
    game = statsapi.get("game", {"gamePk": game_pk})
    game_data = game["gameData"]

    # The game feed already includes the linescore, so no second request is needed
    ls = game.get("liveData", {}).get("linescore", {})

    game_date = game_data["datetime"]["officialDate"] or date.today().strftime('%Y-%m-%d')
    game_status = game_data["status"]["detailedState"]

    innings = ls.get("innings", [])
    game_innings = list(range(1, len(innings) + 1))

    def team_json(side: str) -> dict:
        team = game_data["teams"][side]
        totals = ls.get("teams", {}).get(side, {})
        return {
            "id": team["id"],
            "name": team["name"],
            "teamName": team.get("teamName"),
            "abbr": team.get("abbreviation"),
            "innings": [inn.get(side, {}).get("runs", 0) for inn in innings],
            "R": totals.get("runs"),
            "H": totals.get("hits"),
            "E": totals.get("errors"),
        }

    return {
        "gamePk": game_pk,
        "date": game_date,
        "gameStatus": game_status,
        "gameInnings": game_innings,
        "teams": {
            "home": team_json("home"),
            "away": team_json("away"),
        },
        "nextGame": get_next_game(),
    }


def get_next_game() -> dict:
    """Return info about the Red Sox's next scheduled game, or {"data": "N"} if none."""
    next_game_id = statsapi.next_game(RED_SOX_ID)
    if not next_game_id:
        return {"data": "N"}

    game_data = statsapi.get("game", {"gamePk": next_game_id}).get("gameData", {})
    teams = game_data.get("teams")
    if not teams:
        return {"data": "N"}

    when = game_data["datetime"]
    return {
        "data": "Y",
        "date": when["officialDate"],
        "time": when["time"],
        "ampm": when["ampm"],
        "home": teams["home"]["teamName"],
        "away": teams["away"]["teamName"],
    }


@app.route("/api/redsox_sched")
def game_summary():
    # Show today's game if there is one (the first, if it's a doubleheader),
    # otherwise fall back to the most recent game
    today_games = statsapi.schedule(team=RED_SOX_ID)
    if today_games:
        game_pk = today_games[0]['game_id']
    else:
        game_pk = statsapi.last_game(RED_SOX_ID)

    if not game_pk:
        return jsonify({"error": "No game found"}), 404

    return jsonify(game_to_json(game_pk))


@app.route("/api/redsox_standings")
def standings():
    # standings_data returns structured dicts, keyed by division id:
    # {201: {"div_name": "American League East", "teams": [{"name": ..., "w": 89, ...}]}}
    data = statsapi.standings_data(leagueId=AMERICAN_LEAGUE_ID, division=AL_EAST_ID)
    division = data.get(AL_EAST_ID) or data.get(str(AL_EAST_ID)) or {}

    records = []
    for team in division.get("teams", []):
        records.append({
            "rank": team["div_rank"],
            "team": team["name"],
            "wins": team["w"],
            "losses": team["l"],
            "gb": team["gb"],
            "elim": team["elim_num"],
            "wc_rank": team["wc_rank"],
            "wc_gb": team["wc_gb"],
            "wc_elim": team["wc_elim_num"],
        })

    return jsonify(records)


@app.route("/api/redsox_transactions")
def transactions():
    # Compute dates on each request so they stay current on a long-running server
    today = date.today()
    a_week_ago = today - timedelta(days=7)

    data = statsapi.get('transactions', {
        'teamId': RED_SOX_ID,
        'startDate': a_week_ago.strftime('%Y-%m-%d'),
        'endDate': today.strftime('%Y-%m-%d'),
    })

    records = []
    for transaction in data.get('transactions', []):
        person = transaction.get('person') or {}
        full_name = person.get('fullName')
        person_id = person.get('id')

        # Skip transactions with no player attached
        if not full_name or not person_id:
            continue

        records.append({
            "date": transaction['date'],
            "description": transaction['description'],
            "formatted_link": player_url(full_name, person_id),
            "player": full_name,
        })

    return jsonify(records)


@app.route("/api/redsox_roster")
def roster():
    data = statsapi.get('team_roster', {'teamId': RED_SOX_ID})

    records = []
    for entry in data.get('roster', []):
        person = entry.get('person') or {}
        full_name = person.get('fullName')
        if not full_name:
            continue

        parts = full_name.split()
        sort_name = f"{parts[-1]}, {' '.join(parts[:-1])}"  # "Devers, Rafael"
        position = entry.get('position', {}).get('abbreviation', 'N/A')

        number_str = entry.get('jerseyNumber')  # e.g. "2" or "10"
        if number_str and number_str.isdigit():
            number_display = f"{int(number_str):02d}"  # "02", "10"
        else:
            number_display = None

        records.append({
            "number": number_display,
            "position": position,
            "name": full_name,
            "formatted_link": player_url(full_name, person.get('id')),
            "sortName": sort_name,
        })

    return jsonify(records)


def fetch_team_leaders(season: int) -> list:
    """Return the raw teamLeaders list for a season, or [] if MLB has none yet."""
    try:
        data = statsapi.get('team_leaders', {
            'teamId': RED_SOX_ID,
            'leaderCategories': ",".join(cat for cat, _, _ in LEADER_CATEGORIES),
            'season': season,
            'limit': LEADER_LIMIT,
        })
    except requests.HTTPError as err:
        # MLB answers 404 for a season that hasn't started
        if err.response is not None and err.response.status_code == 404:
            return []
        raise
    return data.get('teamLeaders', [])


@app.route("/api/redsox_leaders")
def leaders():
    # Before Opening Day there are no stats for the new year yet,
    # so fall back to last season's leaders
    season = date.today().year
    team_leaders = fetch_team_leaders(season)
    if not any(group.get('leaders') for group in team_leaders):
        season -= 1
        team_leaders = fetch_team_leaders(season)

    by_category = {
        (group.get('leaderCategory'), group.get('statGroup')): group.get('leaders', [])
        for group in team_leaders
    }

    categories = []
    for category, stat_group, label in LEADER_CATEGORIES:
        players = []
        for leader in by_category.get((category, stat_group), []):
            person = leader.get('person') or {}
            full_name = person.get('fullName')
            person_id = person.get('id')
            if not full_name or not person_id:
                continue
            players.append({
                "rank": leader.get('rank'),
                "name": full_name,
                "value": leader.get('value'),
                "formatted_link": player_url(full_name, person_id),
            })
        categories.append({"label": label, "leaders": players})

    return jsonify({"season": season, "categories": categories})


@app.errorhandler(Exception)
def handle_error(err):
    # If the MLB API is down or returns something unexpected, send JSON
    # with a 502 status instead of Flask's HTML error page
    if isinstance(err, HTTPException):
        return err  # normal errors like 404 Not Found pass through unchanged
    if request.path.startswith("/api/"):
        app.logger.exception("API request failed")
        return jsonify({"error": "Could not load data from MLB"}), 502
    raise err


@app.route("/")
def index():
    return send_from_directory(app.static_folder or "static", "sox_stats.html")


if __name__ == "__main__":
    app.run(debug=True)
