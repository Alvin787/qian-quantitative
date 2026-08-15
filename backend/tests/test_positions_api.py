"""API tests for positions sizing endpoint."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_post_size_happy_path() -> None:
    response = client.post(
        "/api/positions/size",
        json={
            "equity": 100_000,
            "entry_price": 50,
            "final_stop": 49,
            "method": "fixed_pct",
            "risk_pct": 0.5,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["shares"] == 500
    assert body["risk_dollars"] == 500
    assert len(body["stop_book"]) == 3


def test_post_size_bad_entry_stop() -> None:
    response = client.post(
        "/api/positions/size",
        json={
            "equity": 100_000,
            "entry_price": 49,
            "final_stop": 50,
            "method": "fixed_pct",
            "risk_pct": 0.5,
        },
    )
    assert response.status_code == 400
    assert "detail" in response.json()


def test_post_plan_happy_path() -> None:
    response = client.post(
        "/api/positions/plan",
        json={
            "shares": 300,
            "entry_price": 50,
            "final_stop": 49,
            "entry_date": "2026-08-10",
            "as_of_date": "2026-08-10",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["day_index"] == 0
    assert body["phase"] == "day0_init"
    assert body["net_shares"] == 300
    assert len(body["stop_book"]) == 3
    assert body["stop_mode"] == "three_tier"
    assert body["actions"] == []


def test_post_plan_bad_dates() -> None:
    response = client.post(
        "/api/positions/plan",
        json={
            "shares": 300,
            "entry_price": 50,
            "final_stop": 49,
            "entry_date": "2026-08-13",
            "as_of_date": "2026-08-10",
        },
    )
    assert response.status_code == 400
    assert "detail" in response.json()


def test_post_plan_day3_consolidates_be() -> None:
    response = client.post(
        "/api/positions/plan",
        json={
            "shares": 300,
            "entry_price": 50,
            "final_stop": 49,
            "entry_date": "2026-08-10",
            "as_of_date": "2026-08-13",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["day_index"] == 3
    assert body["phase"] == "day3"
    assert body["stop_mode"] == "breakeven"
    codes = [a["code"] for a in body["actions"]]
    assert "DAY3_CONSOLIDATE_BE" in codes
    assert body["stop_book"] == [
        {"label": "BE", "price": 50.0, "shares": 200, "r_fraction": 0.0}
    ]
