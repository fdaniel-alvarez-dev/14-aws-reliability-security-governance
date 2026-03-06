#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _print_err(message: str) -> None:
    sys.stderr.write(message.rstrip() + "\n")


def _run(cmd: list[str], *, cwd: Path) -> int:
    proc = subprocess.run(cmd, cwd=cwd, text=True)
    return proc.returncode


def _mode_from_env_or_arg(mode: str | None) -> str:
    if mode:
        return mode
    return os.environ.get("TEST_MODE", "demo")


def _validate_mode(mode: str) -> None:
    if mode not in {"demo", "production"}:
        raise SystemExit("Invalid mode. Use --mode demo|production or set TEST_MODE=demo|production.")


def run_demo() -> int:
    code = 0
    code |= _run([sys.executable, "-m", "compileall", "-q", "."], cwd=REPO_ROOT)
    code |= _run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-q"],
        cwd=REPO_ROOT,
    )
    return code


def run_production() -> int:
    if os.environ.get("PRODUCTION_TESTS_CONFIRM") != "1":
        _print_err(
            "Production-mode tests are guarded.\n"
            "Set PRODUCTION_TESTS_CONFIRM=1 to confirm you intend to run checks against real system state.\n"
            "Example:\n"
            "  TEST_MODE=production PRODUCTION_TESTS_CONFIRM=1 python3 tests/run_tests.py\n"
        )
        return 2

    ssh_path = os.environ.get("SSH_CONFIG_PATH", "/etc/ssh/sshd_config")
    if not Path(ssh_path).exists():
        _print_err(
            "Missing SSH config file required for production checks.\n"
            f"- Tried: {ssh_path}\n\n"
            "Set SSH_CONFIG_PATH to a valid sshd_config path and rerun:\n"
            "  SSH_CONFIG_PATH=/path/to/sshd_config TEST_MODE=production PRODUCTION_TESTS_CONFIRM=1 python3 tests/run_tests.py\n"
        )
        return 2

    out_path = REPO_ROOT / "artifacts" / "_prod_check_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    code = _run(
        [
            sys.executable,
            str(REPO_ROOT / "pipelines" / "pipeline.py"),
            "--mode",
            "production",
            "--out",
            str(out_path),
            "--ssh-config-path",
            ssh_path,
        ],
        cwd=REPO_ROOT,
    )
    if code != 0:
        return code

    try:
        report = json.loads(out_path.read_text(encoding="utf-8"))
    except Exception as exc:
        _print_err(f"Unable to parse production report JSON: {exc}")
        return 1

    if "checks" not in report or not isinstance(report["checks"], list):
        _print_err("Production report missing expected 'checks' list.")
        return 1

    _print_err(f"Production check OK: wrote {out_path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run repository tests in demo or production mode.")
    parser.add_argument("--mode", choices=["demo", "production"], help="Execution mode.")
    args = parser.parse_args(argv)

    mode = _mode_from_env_or_arg(args.mode)
    _validate_mode(mode)

    if mode == "demo":
        return run_demo()
    return run_production()


if __name__ == "__main__":
    raise SystemExit(main())
