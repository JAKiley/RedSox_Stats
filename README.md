Uses Python, Flask and the MLB Stats API to get the current Red Sox information using HTML and Javascript.

1. Last Red Sox Game Status
2. Current Standings of AL East - the only division that really matters 😁
3. Red Sox Team Leaders - top 3 in Batting Average, Home Runs, RBI, ERA, Wins, Strikeouts and Saves
4. Current Transactions within the past week for the Red Sox
5. Current Red Sox Roster which is sortable clicking on the header

This can be accessed via https://redsox-stats.onrender.com/

To run the tests (they use fake MLB data, so no network is needed):

    pip install -r requirements-dev.txt
    pytest

Thanks to Todd Roberts
https://pypi.org/project/MLB-StatsAPI/
