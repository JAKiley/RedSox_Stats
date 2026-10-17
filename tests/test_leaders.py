from datetime import date

import pytest
import requests

import app as app_module


def leader(rank, name, person_id, value):
    return {"rank": rank, "value": value, "person": {"id": person_id, "fullName": name}}


SAMPLE_LEADERS = {
    "teamLeaders": [
        {
            "leaderCategory": "homeRuns",
            "statGroup": "hitting",
            "leaders": [
                leader(1, "Willson Contreras", 575929, "27"),
                leader(2, "Wilyer Abreu", 677800, "24"),
                leader(3, "Jarren Duran", 680776, "20"),
            ],
        },
        {
            # Home runs allowed by pitchers; must not show up as a hitting leader
            "leaderCategory": "homeRuns",
            "statGroup": "pitching",
            "leaders": [leader(1, "Sonny Gray", 543243, "16")],
        },
        {
            "leaderCategory": "earnedRunAverage",
            "statGroup": "pitching",
            "leaders": [leader(1, "Sonny Gray", 543243, "2.72")],
        },
    ]
}


@pytest.fixture
def client():
    app_module.app.config["TESTING"] = True
    return app_module.app.test_client()


def by_label(payload):
    return {c["label"]: c["leaders"] for c in payload["categories"]}


def test_leaders_groups_by_category_and_stat_group(client, monkeypatch):
    monkeypatch.setattr(app_module.statsapi, "get", lambda endpoint, params: SAMPLE_LEADERS)

    res = client.get("/api/redsox_leaders")

    assert res.status_code == 200
    payload = res.get_json()
    assert payload["season"] == date.today().year
    leaders = by_label(payload)

    assert [p["name"] for p in leaders["Home Runs"]] == [
        "Willson Contreras", "Wilyer Abreu", "Jarren Duran",
    ]
    assert leaders["Home Runs"][0]["value"] == "27"
    assert leaders["Home Runs"][0]["formatted_link"] == (
        "https://www.mlb.com/player/willson-contreras-575929"
    )
    assert [p["value"] for p in leaders["ERA"]] == ["2.72"]
    # Categories MLB returned nothing for still appear, just empty
    assert leaders["Saves"] == []
    assert len(payload["categories"]) == len(app_module.LEADER_CATEGORIES)


def test_leaders_falls_back_to_last_season_when_new_season_is_404(client, monkeypatch):
    this_year = date.today().year
    seasons_requested = []

    def fake_get(endpoint, params):
        seasons_requested.append(params["season"])
        if params["season"] == this_year:
            response = requests.Response()
            response.status_code = 404
            raise requests.HTTPError("404 Not Found", response=response)
        return SAMPLE_LEADERS

    monkeypatch.setattr(app_module.statsapi, "get", fake_get)

    res = client.get("/api/redsox_leaders")

    assert res.status_code == 200
    assert res.get_json()["season"] == this_year - 1
    assert seasons_requested == [this_year, this_year - 1]


def test_leaders_falls_back_when_new_season_has_no_leaders(client, monkeypatch):
    this_year = date.today().year

    def fake_get(endpoint, params):
        if params["season"] == this_year:
            return {"teamLeaders": [{"leaderCategory": "homeRuns", "statGroup": "hitting", "leaders": []}]}
        return SAMPLE_LEADERS

    monkeypatch.setattr(app_module.statsapi, "get", fake_get)

    payload = client.get("/api/redsox_leaders").get_json()

    assert payload["season"] == this_year - 1
    assert by_label(payload)["Home Runs"][0]["name"] == "Willson Contreras"


def test_leaders_returns_502_when_mlb_is_down(client, monkeypatch):
    def fake_get(endpoint, params):
        response = requests.Response()
        response.status_code = 500
        raise requests.HTTPError("500 Server Error", response=response)

    monkeypatch.setattr(app_module.statsapi, "get", fake_get)

    res = client.get("/api/redsox_leaders")

    assert res.status_code == 502
    assert res.get_json() == {"error": "Could not load data from MLB"}
