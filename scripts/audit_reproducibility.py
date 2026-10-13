
"""
AirScope | nik
Reproducibility audit.

Checks repository setup, dependency manifests,
processed datasets, model artifacts, and verification scripts.

Also checks installed runtime versions and Git tracking.

Does not install dependencies, modify datasets,
or retrain machine-learning models.
"""

from pathlib import Path
import platform
import shutil
import subprocess
import sys


# AirScope repository root.
ROOT = Path(__file__).resolve().parents[1]


def display_status(label, exists, required=True):
    """Display whether a project resource exists."""

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
    exists = path.is_file()

    display_status(relative_path, exists, required)

    return exists


def check_command(command):
    """Return a command's version without changing the environment."""

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

        if result.returncode != 0:
            return (
                f"Command failed "
                f"(exit code {result.returncode})"
            )

        return (
            output.splitlines()[0]
            if output
            else "No version output"
        )

    except (FileNotFoundError, OSError):
        return "Not available"


def check_npm():
    """
    Detect npm on Windows, Linux and macOS.

    Windows commonly exposes npm as npm.cmd.
    This avoids incorrectly reporting npm as unavailable.
    """

    if platform.system() == "Windows":
        candidates = ["npm.cmd", "npm"]
    else:
        candidates = ["npm"]

    for candidate in candidates:
        executable = shutil.which(candidate)

        if executable:
            result = check_command(
                [executable, "--version"]
            )

            if not result.startswith(
                ("Not available", "Command failed")
            ):
                return result

    return "Not available"


def section(title):
    """Print a consistent section heading."""

    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


def check_git_tracking(relative_path):
    """Check whether Git tracks a specific project file."""

    try:
        result = subprocess.run(
            [
                "git",
                "ls-files",
                "--error-unmatch",
                "--",
                relative_path,
            ],
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

    except (FileNotFoundError, OSError):
        print(
            f"GIT UNAVAILABLE: {relative_path}"
        )


def main():
    print("=" * 60)
    print("AirScope | Reproducibility Audit")
    print("=" * 60)

    print(f"Repository: {ROOT}")

    # =========================================
    # 1. RUNTIME ENVIRONMENT
    # =========================================
    section("1. Runtime Environment")

    print(f"Python: {sys.version.split()[0]}")
    print(f"OS: {platform.system()}")

    node_version = check_command(
        ["node", "--version"]
    )

    npm_version = check_npm()

    print(f"Node: {node_version}")
    print(f"npm: {npm_version}")

    # =========================================
    # 2. DEPENDENCY CONFIGURATION
    # =========================================
    section("2. Dependency Configuration")

    manifests = [
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "environment.yml",
        "Pipfile",
    ]

    python_manifest_found = False

    for manifest in manifests:
        if check_file(
            manifest,
            required=False,
        ):
            python_manifest_found = True

    if not python_manifest_found:
        print(
            "WARNING: No standard root-level Python "
            "dependency manifest detected."
        )

    check_file("frontend/package.json")
    check_file(
        "frontend/package-lock.json",
        required=False,
    )

    # =========================================
    # 3. APPLICATION ENTRY POINTS
    # =========================================
    section("3. Application Entry Points")

    application_files = [
        "backend/app/main.py",
        "frontend/src/pages/CitiesPage.tsx",
        "frontend/src/components/BerlinForecastPanel.tsx",
        "frontend/src/components/StationHistoryChart.tsx",
    ]

    for file in application_files:
        check_file(file)

    # =========================================
    # 4. PROCESSED DATASETS
    # =========================================
    section("4. Processed Datasets")

    data_files = [
        "data/processed/berlin_pm25_hourly.parquet",
        "data/processed/london_pm25_final.parquet",
        "data/processed/airscope_forecast_features.parquet",
        "data/processed/berlin_station_evaluation.csv",
    ]

    for file in data_files:
        check_file(file)

    # =========================================
    # 5. TRUSTED MODEL ARTIFACTS
    # =========================================
    section("5. Trusted Model Artifacts")

    model_files = [
        "models/berlin_pm25_hgb_6h.joblib",
        "models/berlin_pm25_hgb_12h.joblib",
        "models/berlin_pm25_hgb_24h.joblib",
    ]

    for file in model_files:
        check_file(file)

    # =========================================
    # 6. DOCUMENTATION AND VERIFICATION
    # =========================================
    section("6. Documentation and Verification")

    documentation_files = [
        "README.md",
        "docs/architecture/system_architecture.md",
        "scripts/verify_phase05.py",
        "scripts/verify_end_to_end.py",
        "scripts/inspect_dependencies.py",
    ]

    for file in documentation_files:
        check_file(
            file,
            required=(
                file != "scripts/inspect_dependencies.py"
            ),
        )

    # =========================================
    # 7. GIT TRACKING
    # =========================================
    section("7. Git Tracking")

    resources = [
        "README.md",
        "frontend/package-lock.json",
        *data_files,
        *model_files,
    ]

    for resource in resources:
        check_git_tracking(resource)

    # =========================================
    # AUDIT SUMMARY
    # =========================================
    section("Audit Summary")

    print("Reproducibility audit completed.")

    print(
        "Missing local files and untracked files "
        "are not automatically errors."
    )

    print(
        "Processed datasets and trusted model artifacts "
        "may intentionally be excluded from Git."
    )

    print(
        "A complete fresh-clone reproducibility check "
        "requires dependency installation and "
        "dataset/model regeneration verification."
    )


if __name__ == "__main__":
    main()
