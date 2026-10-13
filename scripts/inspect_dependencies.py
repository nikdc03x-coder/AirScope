
"""
AirScope | nik
Inspect Python dependency versions.

Reads package metadata from the active environment.
Does not install or modify packages.
"""

from importlib.metadata import (
    PackageNotFoundError,
    version,
)

# Main dependencies commonly used by the AirScope
# ingestion, API, ML and evaluation pipelines.
PACKAGES = [
    "fastapi",
    "uvicorn",
    "pandas",
    "numpy",
    "pyarrow",
    "scikit-learn",
    "scipy",
    "joblib",
    "requests",
    "httpx",
    "pytest",
    "pydantic",
    "starlette",
]


def main():
    print("=" * 55)
    print("AirScope | Python Dependency Inspection")
    print("=" * 55)

    for package in PACKAGES:
        try:
            installed_version = version(package)

            print(
                f"{package:<20} "
                f"{installed_version}"
            )

        except PackageNotFoundError:
            print(
                f"{package:<20} "
                "NOT INSTALLED"
            )

    print("=" * 55)


if __name__ == "__main__":
    main()
