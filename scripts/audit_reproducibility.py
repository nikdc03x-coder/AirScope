
"""
AirScope | nik
Reproducibility audit.

Checks repository setup, dependency manifests,
processed datasets, model artifacts, and key scripts.

Does not install dependencies, edit files, or retrain models.
"""

from pathlib import Path
import platform
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]


def display_status(label, exists, required=True):
    """Display whether a project resource is present."""

    if exists:
        status = "PASS"
    elif required:
        status = "MISSING"
    else:
        status = "OPTIONAL"

    print(f"[{status}] {label}")


def check_file(relative_path, required=True):
    """Check whether a repository file exists."""

    path = ROOT / relative_path

    display_status(
        relative_path,
        path.is_file(),
        required,
    )

    return path.is_file()


def check_command(command):
    """Read a tool version without changing the environment."""

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
            cwd=ROOT,
        )

        output = (
            result.stdout.strip()
            or result.stderr.strip()
        )

        return (
            output.splitlines()[0]
            if output
            else "No version output"
        )

    except (FileNotFoundError, OSError):
        return "Not available"


def section(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def main():
    print("AirScope | Reproducibility Audit")
    print(f"Repository: {ROOT}")

    section("1. Runtime Environment")

    print(f"Python: {sys.version.split()[0]}")
    print(f"OS: {platform.system()}")
    print(f"Node: {check_command(['node', '--version'])}")
    print(f"npm: {check_command(['npm', '--version'])}")

    section("2. Dependency Configuration")

    manifests = [
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "environment.yml",
        "Pipfile",
    ]

    python_manifest_found = False

    for item in manifests:
        if check_file(item, required=False):
            python_manifest_found = True

    if not python_manifest_found:
        print(
            "WARNING: No standard root-level Python "
            "dependency manifest detected."
        )

    check_file("frontend/package.json")
    check_file("frontend/package-lock.json", required=False)

    section("3. Application Entry Points")

    check_file("backend/app/main.py")
    check_file("frontend/src/pages/CitiesPage.tsx")
    check_file("frontend/src/components/BerlinForecastPanel.tsx")
    check_file("frontend/src/components/StationHistoryChart.tsx")

    section("4. Processed Datasets")

    data_files = [
        "data/processed/berlin_pm25_hourly.parquet",
        "data/processed/london_pm25_final.parquet",
        "data/processed/airscope_forecast_features.parquet",
        "data/processed/berlin_station_evaluation.csv",
    ]

    for item in data_files:
        check_file(item)

    section("5. Trusted Model Artifacts")

    models = [
        "models/berlin_pm25_hgb_6h.joblib",
        "models/berlin_pm25_hgb_12h.joblib",
        "models/berlin_pm25_hgb_24h.joblib",
    ]

    for item in models:
        check_file(item)

    section("6. Documentation and Verification")

    check_file("README.md")
    check_file("docs/architecture/system_architecture.md")
    check_file("scripts/verify_phase05.py")
    check_file("scripts/verify_end_to_end.py")

    section("7. Git Tracking")

    resources = [
        "README.md",
        "frontend/package-lock.json",
        *data_files,
        *models,
    ]

    for relative_path in resources:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", relative_path],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )

        tracked = result.returncode == 0

        print(
            f"{'TRACKED' if tracked else 'NOT TRACKED'}: "
            f"{relative_path}"
        )

    print("\n" + "=" * 60)
    print("Audit complete.")
    print(
        "Missing local files and untracked files are not "
        "automatically errors."
    )
    print(
        "Large datasets and trained models may be intentionally "
        "excluded from Git."
    )


if __name__ == "__main__":
    main()
