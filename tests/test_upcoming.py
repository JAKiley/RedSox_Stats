from datetime import date, timedelta

import pytest

import app as app_module


def game(**overrides):
    base = {
        "game_id": 1,
        "game_date": "2026-09-24",
        "game_datetime": "2026-09-24T22:45:00Z",
        "status": "Scheduled",
        "away_name": "Cleveland Guardians",
        "home_name": "Boston Red Sox",
        "away_id": 114,
        "home_id": 111,
        "venue_name": "Fenway Park",
        "home_probable_pitcher": "Ranger Suarez",
        "away_probable_pitcher": "Daniel Espino",
    }
    base.update(overrides)
    return base


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def test_upcoming_asks_for_today_through_six_days_out(client, monkeypatch):
    calls = []

    def fake_schedule(**kwargs):
        calls.append(kwargs)
        return []

    monkeypatch.setattr(app_module.statsapi, "schedule", fake_schedule)

    res = client.get("/api/redsox_upcoming")

    assert res.status_code == 200
    assert res.get_json() == []
    today = date.today()
    assert calls == [{
        "team": app_module.RED_SOX_ID,
        "start_date": today.strftime("%Y-%m-%d"),
        "end_date": (today + timedelta(days=6)).strftime("%Y-%m-%d"),
    }]


def test_upcoming_home_game_lists_sox_pitcher_first(client, monkeypatch):
    monkeypatch.setattr(app_module.statsapi, "schedule", lambda **kwargs: [game()])

    [record] = client.get("/api/redsox_upcoming").get_json()

    assert record == {
        "date": "2026-09-24",
        "datetime": "2026-09-24T22:45:00Z",
        "status": "Scheduled",
        "homeAway": "vs",
        "opponent": "Cleveland Guardians",
        "venue": "Fenway Park",
        "soxPitcher": "Ranger Suarez",
        "oppPitcher": "Daniel Espino",
    }


def test_upcoming_road_game_flips_sides_and_fills_tbd(client, monkeypatch):
    road_game = game(
        away_name="Boston Red Sox", away_id=111,
        home_name="New York Yankees", home_id=147,
        venue_name="Yankee Stadium",
        away_probable_pitcher="",
        home_probable_pitcher="Max Fried",
    )
    monkeypatch.setattr(app_module.statsapi, "schedule", lambda **kwargs: [road_game])

    [record] = client.get("/api/redsox_upcoming").get_json()

    assert record["homeAway"] == "at"
    assert record["opponent"] == "New York Yankees"
    assert record["soxPitcher"] == "TBD"
    assert record["oppPitcher"] == "Max Fried"
