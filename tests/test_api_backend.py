from __future__ import annotations

from datetime import datetime, timezone

import pytest

from alert_engine.alerts.scorer import AlertExtras
from alert_engine.config import DEFAULT_CONFIG
from alert_engine.data_sources.details import _best_image_url
from alert_engine.data_sources.photos import _best_photo_image
from alert_engine.models.flight import Flight
from alert_engine.services.airport_scan import (
    InvalidAirportCodeError,
    _operator_display,
    _share_images_by_registration,
    build_flight_links,
    flight_to_api_dict,
    normalize_airport_code,
)


def test_normalize_airport_code_accepts_iata_and_icao() -> None:
    assert normalize_airport_code("pvd") == "PVD"
    assert normalize_airport_code("kbos") == "KBOS"


def test_c919_is_treated_as_rare_aircraft_type() -> None:
    assert "C919" in DEFAULT_CONFIG.rare_aircraft_codes


@pytest.mark.parametrize("value", ["", "12A", "PV12", "ABCDE", "B*O"])
def test_normalize_airport_code_rejects_unsafe_values(value: str) -> None:
    with pytest.raises(InvalidAirportCodeError):
        normalize_airport_code(value)


def test_build_flight_links_prefers_registration_and_fr24_id() -> None:
    flight = Flight(
        flight_number="B61234",
        registration="N123JB",
        aircraft_type="A320",
        operator="JetBlue",
        origin="PVD",
        destination="BOS",
        scheduled_arrival=None,
        estimated_arrival=None,
        fr24_id="abc123",
    )

    links = build_flight_links(flight)

    assert links["fr24"] == "https://www.flightradar24.com/abc123"
    assert links["jetphotos"] == "https://www.jetphotos.com/registration/N123JB"


def test_best_image_url_prefers_larger_aircraft_image() -> None:
    images = [
        {"thumbnails": {"src": "https://example.com/aircraft-thumb-200.jpg"}},
        {"large": {"src": "https://example.com/aircraft-large-1200.jpg"}},
    ]

    assert _best_image_url(images) == "https://example.com/aircraft-large-1200.jpg"


def test_best_photo_image_uses_planespotters_large_thumbnail() -> None:
    photo = {
        "thumbnail": {"src": "https://example.com/thumb.jpg"},
        "thumbnail_large": {"src": "https://example.com/large.jpg"},
    }

    assert _best_photo_image(photo) == "https://example.com/large.jpg"


def test_operator_display_collapses_livery_suffix() -> None:
    assert _operator_display("JetBlue (JetBlue Vacations Livery)") == "JetBlue"
    assert _operator_display("Delta Air Lines (Team USA)") == "Delta Air Lines"


def test_share_images_by_registration_reuses_available_image() -> None:
    arrival = Flight(
        flight_number="B62875",
        registration="N648JB",
        aircraft_type="A320",
        operator="JetBlue",
        origin="MCO",
        destination=None,
        scheduled_arrival=None,
        estimated_arrival=None,
    )
    departure = Flight(
        flight_number="B627",
        registration="N648JB",
        aircraft_type="A320",
        operator="JetBlue",
        origin=None,
        destination="FLL",
        scheduled_arrival=None,
        estimated_arrival=None,
    )
    setattr(arrival, "image_url", "https://example.com/n648jb-large.jpg")

    _share_images_by_registration(
        [
            (arrival, 50, ["Special livery"], AlertExtras()),
            (departure, 50, ["Special livery"], AlertExtras()),
        ]
    )

    assert getattr(departure, "image_url") == "https://example.com/n648jb-large.jpg"


def test_flight_to_api_dict_includes_details_shape() -> None:
    flight = Flight(
        flight_number="B61234",
        registration="N123JB",
        aircraft_type="A320",
        operator="JetBlue",
        origin="PVD",
        destination="BOS",
        scheduled_arrival=datetime(2026, 6, 8, 18, 0, tzinfo=timezone.utc),
        estimated_arrival=None,
        scheduled_departure=None,
        estimated_departure=None,
        fr24_id="abc123",
        movement="arrival",
        source="schedule",
    )
    extras = AlertExtras(
        livery_name="Blue Finest",
        livery_airline="JetBlue",
        livery_description="Special paint",
    )

    payload = flight_to_api_dict(flight, 75, ["special_livery"], extras)

    assert payload["flight_number"] == "B61234"
    assert payload["score"] == 75
    assert payload["reasons"] == ["special_livery"]
    assert payload["livery_name"] == "Blue Finest"
    assert payload["scheduled_arrival"] == "2026-06-08T18:00:00Z"
    assert payload["primary_time_label"] == "arrival"
    assert payload["primary_time"] == "2026-06-08T18:00:00Z"
    assert payload["display_destination"] == "BOS"
    assert payload["links"]["jetphotos"].endswith("/N123JB")
