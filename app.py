# app.py
from flask import Flask, jsonify, send_from_directory
import statsapi
from datetime import date, timedelta
import json

app = Flask(__name__, static_folder="static")
today = date.today()
aweek_ago = date.today() - timedelta(days=7)

@app.route("/api/redsox_sched")
def redsox_api():
    
    games = statsapi.schedule(team=111)
    
    if not games:
        json_string = '{"summary": "No Red Sox game scheduled for today"}'
        games = json.loads(json_string)
    
    return jsonify(games)

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
    
    roster = statsapi.roster(111)   
    
    records = []
    
    for line in roster.splitlines():
        line = line.strip()
        if not line or not line.startswith("#"):
            continue

        line = line[1:].strip()
        parts = line.split()

        if parts[0].isdigit():
            number = parts[0]
            position = parts[1]
            name = " ".join(parts[2:])
            sortName = f"{parts[3]} {parts[2]}"
        else:
            number = ""
            position = parts[0]
            name = " ".join(parts[1:])
            sortName = f"{parts[2]} {parts[1]}"

        records.append({"number": number, "position": position, "name": name, "sortName": sortName})
            
    return jsonify(records)

# Serve your index.html (e.g., in static/index.html)
@app.route("/")
def index():
    return send_from_directory(app.static_folder, "sox_stats.html")

if __name__ == "__main__":
    app.run(debug=True)

