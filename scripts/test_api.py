
"""
AirScope | nik
Smoke-test the local FastAPI backend.

Checks API health, station discovery, and Berlin forecasts.
Requires the FastAPI server to be running on port 8000.
"""

import sys

import httpx


BASE_URL = "http://127.0.0.1:8000"


def get_json(client, endpoint):
    """Request an API endpoint and verify HTTP success."""

    response = client.get(endpoint)
    response.raise_for_status()
    return response.json()


def main():
    print("AirScope | API smoke test")

    try:
        with httpx.Client(
            base_url=BASE_URL,
            timeout=30,
        ) as client:

            # Confirm the backend is accessible.
            health = get_json(
                client, "/api/v1/health"
            )

            assert health["status"] == "ok"
            print("[PASS] Health endpoint")

            # Verify the known Berlin station registry.
            stations = get_json(
                client, "/api/v1/stations"
            )

            station_ids = {
                station["station_id"]
                for station in stations["stations"]
            }

            assert len(station_ids) == 12
            assert "DEBE010" in station_ids

            print("[PASS] Berlin station endpoint")

            # Check actual saved-model inference.
            forecast = get_json(
                client,
                "/api/v1/forecasts/berlin/DEBE010",
            )

            horizons = {
                item["horizon_hours"]
                for item in forecast["predictions"]
            }

            assert horizons == {6, 12, 24}
            assert forecast["is_live"] is False

            for prediction in forecast["predictions"]:
                assert isinstance(
                    prediction["predicted_pm25_ugm3"],
                    (int, float),
                )

            print("[PASS] Berlin forecast endpoint")

            print("\nForecast origin:")
            print(forecast["forecast_origin_utc"])

            print("\nGenerated predictions:")

            for prediction in forecast["predictions"]:
                print(
                    f"{prediction['horizon_hours']}h: "
                    f"{prediction['predicted_pm25_ugm3']} "
                    "µg/m³"
                )

            # Check the allowed React development origin.
            response = client.options(
                "/api/v1/stations",
                headers={
                    "Origin": "http://localhost:5173",
                    "Access-Control-Request-Method": "GET",
                },
            )

            response.raise_for_status()

            allowed_origin = response.headers.get(
                "access-control-allow-origin"
            )

            assert allowed_origin == "http://localhost:5173"

            print("\n[PASS] React frontend CORS access")

    except (
        httpx.HTTPError,
        AssertionError,
        KeyError,
        TypeError,
    ) as error:
        print(f"\n[FAIL] {type(error).__name__}: {error}")
        sys.exit(1)

    print("\nAll AirScope API checks passed.")


if __name__ == "__main__":
    main()
