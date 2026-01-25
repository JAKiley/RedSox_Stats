# app.py
from flask import Flask, jsonify, send_from_directory
import statsapi
from datetime import date, timedelta
import requests

app = Flask(__name__, static_folder="static")
today = date.today()
aweek_ago = date.today() - timedelta(days=7)

def game_to_json(game_pk: int) -> dict:
    game = statsapi.get("game", {"gamePk": game_pk})
    
    ls = requests.get(f"https://statsapi.mlb.com/api/v1/game/{game_pk}/linescore").json()
    
    game_date = game["gameData"]["datetime"]["officialDate"]
    game_status = game["gameData"]["status"]["detailedState"]

    home_team = game["gameData"]["teams"]["home"]
    away_team = game["gameData"]["teams"]["away"]

    innings = ls.get("innings", [])
    home_innings = [inn.get("home", {}).get("runs", 0) for inn in innings]
    away_innings = [inn.get("away", {}).get("runs", 0) for inn in innings]
    game_innings = list(zip(range(1, len(away_innings) + 1)))    

    home_totals = ls.get("teams", {}).get("home", {})
    away_totals = ls.get("teams", {}).get("away", {})

    return {
        "gamePk": game_pk,
        "date": game_date,
        "gameStatus": game_status,
        "gameInnings": game_innings,
        "teams": {
            "home": {
                "id": home_team["id"],
                "name": home_team["name"],
                "teamName": home_team.get("teamName"),
                "abbr": home_team.get("abbreviation"),
                "innings": home_innings,
                "R": home_totals.get("runs"),
                "H": home_totals.get("hits"),
                "E": home_totals.get("errors"),
            },
            "away": {
                "id": away_team["id"],
                "name": away_team["name"],
                "teamName": away_team.get("teamName"),
                "abbr": away_team.get("abbreviation"),
                "innings": away_innings,
                "R": away_totals.get("runs"),
                "H": away_totals.get("hits"),
                "E": away_totals.get("errors"),
            },
        },
    }

@app.route("/api/redsox_sched")
def redsox_api():
    game_pk = statsapi.last_game(111)
    payload = game_to_json(game_pk)
    return jsonify(payload)

@app.route("/api/redsox_standings")
def redsox_api2():
    
    standing = statsapi.standings(leagueId=103, division=201)
    
# American League East Standings
# Rank Team                   W   L   GB  (E#) WC Rank WC GB (E#)
#  1   Toronto Blue Jays     94  68   -    -      -      -    -  
#  2   New York Yankees      94  68   -    1      1      -    -  
#  3   Boston Red Sox        89  73  5.0   E      2    +2.0   -  
#  4   Tampa Bay Rays        77  85  17.0  E      7    10.0   E  
#  5   Baltimore Orioles     75  87  19.0  E      9    12.0   E  
    records = []
    
    if not standing:
        return jsonify(records)
    
    for line in standing.splitlines():
        # Remove leading/trailing whitespace
        line = line.strip()
        
        # Skip empty lines and lines starting with 'A' or 'R'
        if not line or (line.startswith("A") or line.startswith("R")):
            continue

        parts = line.split()
        
        # 1. Optional rank
        if parts[0].isdigit():
            rank = parts[0]
            parts = parts[1:]  # drop rank from the list
        else:
            rank = ""

        # 2. Find index of the first number = wins
        win_index = next(i for i, p in enumerate(parts) if p.replace('.', '', 1).isdigit())

        # 3. Team name = everything before wins
        team = " ".join(parts[:win_index])

        # 4. Wins / losses
        wins = int(parts[win_index])
        losses = int(parts[win_index + 1])

        # 5. Remaining fields after wins/losses
        remaining = parts[win_index + 2:]  # GB and beyond

        gb = remaining[0] if len(remaining) > 0 else ""
        elim = remaining[1] if len(remaining) > 1 else ""
        wc_rank = remaining[2] if len(remaining) > 2 else ""
        wc_gb = remaining[3] if len(remaining) > 3 else ""
        wc_elim = remaining[4] if len(remaining) > 4 else ""

        # Optionally strip parentheses like "(E#)" → "E#" or "--"
        elim = elim.strip("()") if elim else ""
        wc_elim = wc_elim.strip("()") if wc_elim else ""

        records.append({"rank": rank,
        "team": team,
        "wins": wins,
        "losses": losses,
        "gb": gb,
        "elim": elim,
        "wc_rank": wc_rank,
        "wc_gb": wc_gb,
        "wc_elim": wc_elim})   
        
    return jsonify(records)

@app.route("/api/redsox_transactions")
def redsox_api3():
    
    transactions = statsapi.get('transactions', {
        'teamId': 111,
        'startDate': aweek_ago.strftime('%Y-%m-%d'),
        'endDate': today.strftime('%Y-%m-%d')
        })
    
    records = []

    if not transactions:
        return jsonify(records)
    
    for transaction in transactions.get('transactions', []):
        person = transaction.get('person')

        if not person:
            # No person attached to this transaction
            continue

        full_name = person.get('fullName')
        person_id = person.get('id')

        if not full_name or not person_id:
            continue

        link = f"https://www.mlb.com/player/{full_name}-{person_id}"
        formatted_link = link.lower().replace(" ", "-")

        records.append({
            "date": transaction['date'],
            "description": transaction['description'],
                "formatted_link": formatted_link,
                "player": full_name
        })  
            
    return jsonify(records)

@app.route("/api/redsox_roster")
def redsox_api4():
    
    teamRoster = statsapi.get('team_roster', {
    'teamId': 111, 
})

    records = []
    for roster in teamRoster.get('roster', []):
        person = roster.get('person')

        if not person:
            continue
        full_name = person.get('fullName')
        player_id = person.get('id')
        name_slug = full_name.lower().replace(" ", "-")
        formatted_link = f"https://www.mlb.com/player/{name_slug}-{player_id}"

        if not full_name:
            continue
        parts = full_name.split()
        last = parts[-1]
        first = " ".join(parts[:-1])
        sortName = f"{last}, {first}"
        position = roster.get('position', {}).get('abbreviation', 'N/A')
        number = roster.get('jerseyNumber', 'N/A')

        records.append({
        "number": number,
        "position": position,
        "name": full_name,
        "formatted_link": formatted_link,
        "sortName": sortName
    })
            
    return jsonify(records)

# Serve your index.html (e.g., in static/index.html)
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "sox_stats.html")

if __name__ == "__main__":
    app.run(debug=True)

