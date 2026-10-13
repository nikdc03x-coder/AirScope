
"""
AirScope | nik
End-to-end backend validation.

Uses FastAPI TestClient to exercise the actual
application routes without starting Uvicorn.

Reads existing trusted datasets and model artifacts.
Does not train or modify models.
"""

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def check(response, label):
    """Assert successful API response and print its status."""

    assert response.status_code == 200, (
        f"{label} failed: HTTP {response.status_code}\n"
        f"{response.text[:1000]}"
    )

    print(f"PASS: {label}")

    return response.json()


def test_health():
    result = check(
        client.get("/api/v1/health"),
        "API health",
    )

    assert result["status"] == "ok"


def test_stations():
    result = check(
        client.get("/api/v1/stations"),
        "Berlin stations",
    )

    assert result["station_count"] == 12

    ids = {
        item["station_id"]
        for item in result["stations"]
    }

    assert "DEBE010" in ids


def test_history(city, station_id):
    for days in (7, 30):
        result = check(
            client.get(
                f"/api/v1/observations/{city}/{station_id}",
                params={"days": days},
            ),
            f"{city} {days}-day history",
        )

        assert result["is_live"] is False
        assert result["station_id"] == station_id
        assert result["total_hour_slots"] == days * 24
        assert len(result["observations"]) == days * 24

        assert (
            result["available_measurements"]
            + result["missing_measurements"]
            == days * 24
        )


def test_forecasting():
    result = check(
        client.get(
            "/api/v1/forecasts/berlin/DEBE010"
        ),
        "Berlin ML forecasting",
    )

    assert result["is_live"] is False

    predictions = result["predictions"]

    assert len(predictions) == 3

    horizons = {
        item["horizon_hours"]
        for item in predictions
    }

    assert horizons == {6, 12, 24}

    for item in predictions:
        value = item["predicted_pm25_ugm3"]

        assert isinstance(value, (int, float))
        assert value >= 0


def test_evaluation():
    for horizon in (6, 12, 24):
        result = check(
            client.get(
                "/api/v1/evaluation/berlin/stations",
                params={"horizon": horizon},
            ),
            f"{horizon}h station evaluation",
        )

        assert result["is_live"] is False
        assert result["station_count"] == 12
        assert len(result["stations"]) == 12


def test_invalid_requests():
    # Unknown Berlin station should not return success.
    response = client.get(
        "/api/v1/observations/berlin/UNKNOWN"
    )

    assert response.status_code == 404

    # Unsupported evaluation horizon should be rejected.
    response = client.get(
        "/api/v1/evaluation/berlin/stations",
        params={"horizon": 5},
    )

    assert response.status_code == 422

    print("PASS: Invalid requests rejected")


def main():
    print("=" * 60)
    print("AirScope | End-to-End Validation")
    print("=" * 60)

    test_health()
    test_stations()

    test_history("berlin", "DEBE010")
    test_history("london", "CLL2")

    test_forecasting()
    test_evaluation()
    test_invalid_requests()

    print("\nAll backend end-to-end tests passed.")


if __name__ == "__main__":
    main()
