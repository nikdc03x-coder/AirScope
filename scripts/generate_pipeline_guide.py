
"""
AirScope | nik
Generate a draft pipeline execution guide.

Inspects existing Python scripts and reports:
- Available script entry points
- Possible execution commands
- Referenced CSV, Parquet and model files

Safety:
- Does not run ingestion or training
- Does not overwrite generated datasets
- Does not load model artifacts
- Does not modify existing documentation
"""

import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCE_DIRECTORIES = [
    ROOT / "data",
    ROOT / "ml",
    ROOT / "scripts",
]

OUTPUT = (
    ROOT
    / "docs"
    / "reproducibility"
    / "pipeline_execution.md"
)

EXCLUDED = {
    "__pycache__",
    ".venv",
    ".venv-clean",
}


def find_scripts():
    """Discover Python scripts in pipeline directories."""

    scripts = []

    for directory in SOURCE_DIRECTORIES:
        if not directory.is_dir():
            continue

        for path in directory.rglob("*.py"):
            if any(part in EXCLUDED for part in path.parts):
                continue

            scripts.append(path)

    return sorted(set(scripts))


def has_main_block(tree):
    """Identify direct script execution entry points."""

    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue

        try:
            expression = ast.unparse(node.test)
        except (ValueError, AttributeError):
            continue

        if (
            "__name__" in expression
            and "__main__" in expression
            and "==" in expression
        ):
            return True

    return False


def inspect_script(path):
    """Statically inspect a Python script."""

    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))

    references = set()

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
        ):
            value = node.value.strip()

            if (
                len(value) < 250
                and any(
                    ext in value
                    for ext in (
                        ".csv",
                        ".parquet",
                        ".joblib",
                        ".json",
                    )
                )
            ):
                references.add(value)

    relative_path = path.relative_to(ROOT)

    return {
        "path": relative_path.as_posix(),
        "command": (
            "python -m "
            + ".".join(relative_path.with_suffix("").parts)
            if has_main_block(tree)
            else None
        ),
        "references": sorted(references),
    }


def build_markdown(inventory):
    """Create a reviewable Markdown guide."""

    lines = [
        "# AirScope — Pipeline Execution Guide",
        "",
        "> Generated inventory. Commands are candidates,",
        "> not yet verified regeneration instructions.",
        "",
        "## Intended pipeline",
        "",
        "1. Ingest official Berlin UBA observations.",
        "2. Ingest official London DEFRA observations.",
        "3. Validate and normalize timestamps.",
        "4. Create chronological forecasting features.",
        "5. Train Berlin 6h, 12h and 24h models.",
        "6. Evaluate models against persistence.",
        "7. Generate station-level evaluation reports.",
        "8. Serve stored results through FastAPI.",
        "",
        "## Discovered Python entry points",
        "",
        "| Script | Candidate command |",
        "|---|---|",
    ]

    for item in inventory:
        command = item["command"]

        if command:
            lines.append(
                f"| `{item['path']}` | `{command}` |"
            )

    lines.extend([
        "",
        "## Referenced data and model files",
        "",
    ])

    for item in inventory:
        if not item["references"]:
            continue

        lines.append(f"### `{item['path']}`")
        lines.append("")

        for reference in item["references"]:
            lines.append(f"- `{reference}`")

        lines.append("")

    lines.extend([
        "## Verification commands",
        "",
        "These commands validate existing local artifacts:",
        "",
        "```bash",
        "python -m scripts.verify_phase05",
        "python -m scripts.verify_end_to_end",
        "```",
        "",
        "## Safety and reproducibility notes",
        "",
        "- Do not execute ingestion or training scripts",
        "  before reviewing their input and output paths.",
        "- Some scripts may overwrite existing artifacts.",
        "- Official source data may change over time.",
        "- Model results may differ if source snapshots",
        "  or dependency versions change.",
        "- A main block does not guarantee a module",
        "  can be executed successfully.",
        "",
        "## Manual verification still required",
        "",
        "For each pipeline stage, confirm:",
        "",
        "- Exact command-line arguments",
        "- Required input files",
        "- Expected output files",
        "- Whether existing files are overwritten",
        "- Expected data schema",
        "- Network requirements",
        "- Model evaluation consistency",
        "",
        "---",
        "",
        "AirScope | nik",
        "",
    ])

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("AirScope | Pipeline Guide Generator")
    print("=" * 60)

    inventory = []

    for path in find_scripts():
        try:
            inventory.append(inspect_script(path))
        except (SyntaxError, UnicodeDecodeError) as error:
            print(f"Skipped {path.name}: {error}")

    if OUTPUT.exists():
        raise SystemExit(
            f"Refusing to overwrite existing guide: {OUTPUT}"
        )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    OUTPUT.write_text(
        build_markdown(inventory),
        encoding="utf-8",
    )

    commands = sum(
        item["command"] is not None
        for item in inventory
    )

    print(f"Inspected scripts: {len(inventory)}")
    print(f"Candidate commands: {commands}")
    print(f"Created: {OUTPUT.relative_to(ROOT)}")
    print(
        "Review generated commands before executing them."
    )


if __name__ == "__main__":
    main()
