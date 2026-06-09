from __future__ import annotations

from fastapi.testclient import TestClient

import api.main as api_main


def setup_function() -> None:
    api_main._cache.clear()
    api_main._rate_buckets.clear()


def test_health_route() -> None:
    with TestClient(api_main.app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_scan_route_validates_airport_code() -> None:
    with TestClient(api_main.app) as client:
        response = client.get("/api/scan", params={"airport": "P12"})

    assert response.status_code == 400
    assert response.json()["detail"] == "Airport code must be 3 or 4 letters."


def test_scan_route_returns_and_caches_payload(monkeypatch) -> None:
    calls = {"count": 0}

    def fake_scan_airport_once(code: str, **_: object) -> dict:
        calls["count"] += 1
        return {
            "airport": code,
            "queried_at": "2026-06-08T18:10:00Z",
            "count": 0,
            "cached": False,
            "cache_age_seconds": None,
            "flights": [],
        }

    monkeypatch.setattr(api_main, "scan_airport_once", fake_scan_airport_once)

    with TestClient(api_main.app) as client:
        first = client.get("/api/scan", params={"airport": "pvd"})
        second = client.get("/api/scan", params={"airport": "PVD"})

    assert first.status_code == 200
    assert first.json()["airport"] == "PVD"
    assert first.json()["cached"] is False
    assert second.status_code == 200
    assert second.json()["cached"] is True
    assert calls["count"] == 1
