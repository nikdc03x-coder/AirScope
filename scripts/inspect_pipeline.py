
"""
AirScope | nik
Inspect the existing data and ML pipeline.

Reports Python scripts, main entry points,
and references to datasets or model artifacts.

Read-only: does not execute ingestion, training,
or evaluation scripts.
"""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCE_DIRECTORIES = [
    ROOT / "data",
    ROOT / "ml",
    ROOT / "scripts",
]

EXCLUDED_DIRECTORIES = {
    "__pycache__",
    ".venv",
    ".venv-clean",
}


def find_python_files():
    """Find project Python files in relevant directories."""

    files = []

    for directory in SOURCE_DIRECTORIES:
        if not directory.exists():
            continue

        for path in directory.rglob("*.py"):
            if any(
                part in EXCLUDED_DIRECTORIES
                for part in path.parts
            ):
                continue

            files.append(path)

    return sorted(set(files))


def has_main_entry(tree):
    """Detect an if __name__ == '__main__' block."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue

        try:
            expression = ast.unparse(node.test)
        except (AttributeError, ValueError):
            continue

        if (
            "__name__" in expression
            and "__main__" in expression
            and "==" in expression
        ):
            return True

    return False


def inspect_file(path):
    """Extract useful static information from a script."""

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    referenced_files = set()
    functions = []

    for node in ast.walk(tree):
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef),
        ):
            functions.append(node.name)

        elif isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                value = node.value

                if any(
                    extension in value
                    for extension in (
                        ".csv",
                        ".parquet",
                        ".joblib",
                        ".json",
                    )
                ):
                    referenced_files.add(value)

    return {
        "has_main": has_main_entry(tree),
        "functions": sorted(set(functions)),
        "references": sorted(referenced_files),
    }


def main():
    print("=" * 65)
    print("AirScope | Pipeline Inventory")
    print("=" * 65)

    files = find_python_files()

    print(f"Python files discovered: {len(files)}")

    for path in files:
        relative = path.relative_to(ROOT)

        print("\n" + "-" * 65)
        print(f"FILE: {relative}")
        print("-" * 65)

        try:
            info = inspect_file(path)

        except (SyntaxError, UnicodeDecodeError) as error:
            print(f"Unable to inspect: {error}")
            continue

        print(
            "CLI entry point: "
            + ("YES" if info["has_main"] else "NO")
        )

        if info["has_main"]:
            module_name = ".".join(
                relative.with_suffix("").parts
            )

            print(
                f"Possible command: python -m {module_name}"
            )

        if info["functions"]:
            print(
                "Functions: "
                + ", ".join(info["functions"][:15])
            )

        if info["references"]:
            print("Referenced filenames:")

            for reference in info["references"][:20]:
                print(f"  - {reference}")

    print("\n" + "=" * 65)
    print("Inventory complete.")
    print(
        "Possible commands are inferred from source structure. "
        "They are not guaranteed to work until tested."
    )


if __name__ == "__main__":
    main()
