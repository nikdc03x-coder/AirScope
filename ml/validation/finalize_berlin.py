
"""
AirScope | nik
Finalize Berlin PM2.5 data quality.

Document source gaps, verify recovery responses,
and produce an auditable station-level quality report.

Original measurements are never modified.
"""

import json
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[2]

DATA_FILE = ROOT / "data/processed/berlin_pm25_hourly.parquet"
STATIONS_FILE = ROOT / "data/processed/berlin_pm25_stations.csv"

RECOVERY_DIR = ROOT / "data/raw/uba_gap_recovery"

REPORT_FILE = ROOT / "data/processed/berlin_final_quality.csv"
SUMMARY_FILE = ROOT / "data/processed/berlin_final_summary.json"

START = pd.Timestamp("2025-01-01 00:00:00", tz="UTC")
END = pd.Timestamp("2026-10-11 23:00:00", tz="UTC")

SOURCE_GAPS = [
    {
        "start": "2026-08-15 00:00:00+00:00",
        "end": "2026-08-23 23:00:00+00:00",
        "hours": 216,
    },
    {
        "start": "2026-09-11 13:00:00+00:00",
        "end": "2026-09-13 23:00:00+00:00",
        "hours": 59,
    },
    {
        "start": "2026-09-19 00:00:00+00:00",
        "end": "2026-09-19 23:00:00+00:00",
        "hours": 24,
    },
]


def check_recovery(df, station_id="DEBE010"):
    """Check whether recovery records fill any missing UTC hours."""

    station = df[df["station_id"] == station_id]

    existing = set(station["timestamp_utc"])

    # UBA source JSON uses fixed CET (UTC+01:00).
    # Source dictionary keys are measurement start times.
    recovered = set()

    for path in sorted(
        RECOVERY_DIR.glob(f"{station_id}_*.json")
    ):
        payload = json.loads(
            path.read_text(encoding="utf-8")
        )

        data = payload.get("data", {})

        for observations in data.values():
            for source_start in observations:
                timestamp = pd.Timestamp(source_start)

                # Source start time is CET.
                # Measurement ends one hour later.
                end_utc = (
                    timestamp
                    .tz_localize("Etc/GMT-1")
                    .tz_convert("UTC")
                    + pd.Timedelta(hours=1)
                )

                recovered.add(end_utc)

    new_hours = recovered - existing

    return {
        "recovery_records_checked": len(recovered),
        "new_hours_found": len(new_hours),
        "new_hour_examples": [
            str(value)
            for value in sorted(new_hours)[:10]
        ],
    }


def build_station_report(df):
    """Calculate quality metrics across the expected timeline."""

    expected = pd.date_range(
        START,
        END,
        freq="h",
    )

    expected_hours = len(expected)

    rows = []

    for station_id, station in df.groupby("station_id"):
        observed = pd.DatetimeIndex(
            station["timestamp_utc"]
        )

        missing_hours = expected.difference(observed)

        rows.append({
            "station_id": station_id,
            "station_name": station["station_name"].iloc[0],
            "expected_hours": expected_hours,
            "observed_hours": len(station),
            "missing_hour_slots": len(missing_hours),
            "missing_pm25_values": int(
                station["pm25_ugm3"].isna().sum()
            ),
            "valid_measurements": int(
                station["pm25_ugm3"].notna().sum()
            ),
            "valid_measurement_coverage_pct": round(
                100 * station["pm25_ugm3"].notna().sum()
                / expected_hours,
                2,
            ),
        })

    return pd.DataFrame(rows)


def main():
    print("AirScope | Finalize Berlin PM2.5 quality")

    df = pd.read_parquet(DATA_FILE)

    if df.empty:
        raise ValueError("Berlin dataset is empty.")

    duplicates = df.duplicated(
        ["station_id", "timestamp_utc"]
    ).sum()

    if duplicates:
        raise ValueError(
            f"Duplicate station-hours: {duplicates}"
        )

    recovery = check_recovery(df)

    print("\nTargeted recovery check")
    print(
        "Recovery timestamps checked:",
        recovery["recovery_records_checked"],
    )
    print(
        "New hourly observations:",
        recovery["new_hours_found"],
    )

    if recovery["new_hours_found"]:
        raise RuntimeError(
            "Recovery returned new timestamps. "
            "Review them before finalizing."
        )

    report = build_station_report(df)

    if report["missing_hour_slots"].nunique() != 1:
        raise RuntimeError(
            "Berlin stations have different missing-hour counts. "
            "Recheck source gaps."
        )

    REPORT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    report.to_csv(REPORT_FILE, index=False)

    summary = {
        "project": "AirScope",
        "city": "Berlin",
        "pollutant": "PM2.5",
        "unit": "ug/m3",
        "source": "Umweltbundesamt (UBA)",
        "start_utc": str(START),
        "end_utc": str(END),
        "station_count": int(df["station_id"].nunique()),
        "total_records": int(len(df)),
        "missing_values": int(df["pm25_ugm3"].isna().sum()),
        "missing_hour_slots_total": int(
            report["missing_hour_slots"].sum()
        ),
        "known_shared_source_gaps": SOURCE_GAPS,
        "targeted_recovery": recovery,
        "station_quality_report": str(
            REPORT_FILE.relative_to(ROOT)
        ),
    }

    SUMMARY_FILE.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print("\nFinal Berlin quality report")
    print(report.to_string(index=False))

    print(f"\nSaved: {REPORT_FILE.relative_to(ROOT)}")
    print(f"Saved: {SUMMARY_FILE.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
