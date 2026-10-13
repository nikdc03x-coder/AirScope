
"""
AirScope | nik
Generate Python dependency manifests.

Reads installed package versions from the active
Python environment.

Generates:
- requirements.txt
- requirements-dev.txt

Also reports external imports that need review.
"""

import ast
from importlib.metadata import (
    PackageNotFoundError,
    version,
)
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Core dependencies used by the current AirScope stack.
CORE_PACKAGES = [
    "fastapi",
    "uvicorn",
    "pandas",
    "numpy",
    "pyarrow",
    "scikit-learn",
    "joblib",
    "requests",
]

# Development and API-testing dependencies.
DEV_PACKAGES = [
    "httpx",
    "pytest",
]

# Known import names that differ from package names.
IMPORT_TO_PACKAGE = {
    "sklearn": "scikit-learn",
    "PIL": "Pillow",
    "yaml": "PyYAML",
    "dotenv": "python-dotenv",
    "bs4": "beautifulsoup4",
}

# Directories containing our Python source.
SOURCE_DIRECTORIES = [
    "backend",
    "ml",
    "scripts",
    "data",
]


def installed_version(package):
    """Return the installed version of a package."""

    try:
        return version(package)
    except PackageNotFoundError:
        return None


def write_requirements(path, packages, header):
    """Write pinned versions for installed packages."""

    lines = [
        f"# AirScope | nik",
        f"# {header}",
        "# Generated from the active project environment.",
        "",
    ]

    missing = []

    for package in packages:
        package_version = installed_version(package)

        if package_version is None:
            missing.append(package)
            continue

        lines.append(
            f"{package}=={package_version}"
        )

    path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )

    return missing


def inspect_imports():
    """Collect top-level imports from project Python files."""

    imports = set()

    for directory in SOURCE_DIRECTORIES:
        source = ROOT / directory

        if not source.exists():
            continue

        for path in source.rglob("*.py"):
            try:
                tree = ast.parse(
                    path.read_text(encoding="utf-8")
                )
            except (SyntaxError, UnicodeDecodeError):
                continue

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(
                            alias.name.split(".")[0]
                        )

                elif isinstance(node, ast.ImportFrom):
                    if node.level == 0 and node.module:
                        imports.add(
                            node.module.split(".")[0]
                        )

    return imports


def main():
    print("=" * 60)
    print("AirScope | Dependency Manifest Generator")
    print("=" * 60)

    core_path = ROOT / "requirements.txt"
    dev_path = ROOT / "requirements-dev.txt"

    # Don't silently overwrite existing dependency files.
    for path in (core_path, dev_path):
        if path.exists():
            raise SystemExit(
                f"Refusing to overwrite existing file: {path}"
            )

    # Verify all required packages before writing either file.
    missing_packages = [
        package
        for package in CORE_PACKAGES + DEV_PACKAGES
        if installed_version(package) is None
    ]

    if missing_packages:
        raise SystemExit(
            "Missing installed packages: "
            + ", ".join(missing_packages)
            + "\nReview these packages before generating manifests."
        )

    write_requirements(
        core_path,
        CORE_PACKAGES,
        "Core application, ingestion and ML dependencies.",
    )

    # Development dependencies extend the core environment.
    dev_lines = [
        "# AirScope | nik",
        "# Install development tools alongside core requirements.",
        "",
        "-r requirements.txt",
        "",
    ]

    for package in DEV_PACKAGES:
        dev_lines.append(
            f"{package}=={installed_version(package)}"
        )

    dev_path.write_text(
        "\n".join(dev_lines) + "\n",
        encoding="utf-8",
    )

    print(f"Created: {core_path.name}")
    print(f"Created: {dev_path.name}")

    print("\nInstalled project dependencies:")
    for package in CORE_PACKAGES + DEV_PACKAGES:
        print(
            f"  {package}=={installed_version(package)}"
        )

    # Import audit helps catch missing direct dependencies.
    print("\nPython imports detected in project:")

    for module in sorted(inspect_imports()):
        package = IMPORT_TO_PACKAGE.get(module, module)
        print(f"  {module} -> {package}")

    print(
        "\nReview imports for additional external libraries "
        "before considering the files complete."
    )

    print(
        "\nDo not assume a successful generation proves "
        "that a fresh installation works."
    )


if __name__ == "__main__":
    main()
