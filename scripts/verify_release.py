
"""
AirScope | nik
Final release-readiness verification.

Checks the application and its existing artifacts.
Does not download data, retrain models, or change Git branches.

Run:
    python -m scripts.verify_release
"""

from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"

RESULTS = []


def run_check(name, command, cwd=ROOT):
    """Execute a command and record whether it succeeds."""

    print("\n" + "=" * 60)
    print(name)
    print("=" * 60)

    print("Command:", " ".join(command))

    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )

    except OSError as error:
        print(f"FAIL: {error}")
        RESULTS.append((name, False))
        return

    if result.stdout:
        print(result.stdout)

    if result.stderr:
        print(result.stderr)

    success = result.returncode == 0

    print(
        f"{'PASS' if success else 'FAIL'}: {name}"
    )

    RESULTS.append((name, success))


def check_files():
    """Check required project documentation and manifests."""

    print("\n" + "=" * 60)
    print("Required Project Files")
    print("=" * 60)

    files = [
        "README.md",
        "requirements.txt",
        "requirements-dev.txt",
        "docs/architecture/system_architecture.md",
        "docs/reproducibility/data_and_models.md",
        "docs/reproducibility/pipeline_execution.md",
        "frontend/package.json",
        "frontend/package-lock.json",
    ]

    success = True

    for relative_path in files:
        path = ROOT / relative_path
        exists = path.is_file() and path.stat().st_size > 0

        print(
            f"{'PASS' if exists else 'MISSING'}: "
            f"{relative_path}"
        )

        if not exists:
            success = False

    RESULTS.append(("Required project files", success))


def check_git():
    """Report branch and working tree state."""

    print("\n" + "=" * 60)
    print("Git Status")
    print("=" * 60)

    branch = subprocess.run(
        ["git", "branch", "--show-current"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    status = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    current_branch = branch.stdout.strip()

    print(f"Branch: {current_branch}")

    if status.stdout.strip():
        print("Working tree has pending changes:")
        print(status.stdout)
    else:
        print("Working tree is clean.")

    # A verification script cannot be tracked before
    # its first commit, so only report Git state here.
    RESULTS.append(
        (
            "Expected Git branch",
            branch.returncode == 0
            and current_branch == "phase-07-final-validation",
        )
    )


def main():
    print("=" * 60)
    print("AirScope | Final Release Readiness")
    print("=" * 60)

    print(f"Repository: {ROOT}")
    print(f"Python: {sys.executable}")

    check_files()

    run_check(
        "Python Dependency Compatibility",
        [sys.executable, "-m", "pip", "check"],
    )

    run_check(
        "Phase 5 Scientific Verification",
        [sys.executable, "-m", "scripts.verify_phase05"],
    )

    run_check(
        "Backend End-to-End Verification",
        [sys.executable, "-m", "scripts.verify_end_to_end"],
    )

    run_check(
        "Pipeline Artifact Verification",
        [sys.executable, "-m", "scripts.verify_pipeline_artifacts"],
    )

    # Windows usually exposes npm as npm.cmd.
    npm = "npm.cmd" if sys.platform == "win32" else "npm"

    run_check(
        "Frontend ESLint",
        [npm, "run", "lint"],
        cwd=FRONTEND,
    )

    run_check(
        "Frontend Production Build",
        [npm, "run", "build"],
        cwd=FRONTEND,
    )

    check_git()

    print("\n" + "=" * 60)
    print("RELEASE VERIFICATION SUMMARY")
    print("=" * 60)

    for name, success in RESULTS:
        print(
            f"{'PASS' if success else 'FAIL'}: {name}"
        )

    failures = [
        name
        for name, success in RESULTS
        if not success
    ]

    if failures:
        print(
            f"\nRelease verification incomplete: "
            f"{len(failures)} checks failed."
        )
        raise SystemExit(1)

    print(
        "\nAll automated release checks passed."
    )
    print(
        "Clean-clone reproduction and manual UI review "
        "must still be verified separately."
    )


if __name__ == "__main__":
    main()
