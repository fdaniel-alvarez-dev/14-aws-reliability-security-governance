from __future__ import annotations

import argparse
import json
import os
import platform
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


DEMO_OS_RELEASE = """NAME="Ubuntu"
VERSION="22.04.4 LTS (Jammy Jellyfish)"
ID=ubuntu
ID_LIKE=debian
PRETTY_NAME="Ubuntu 22.04.4 LTS"
VERSION_ID="22.04"
"""

DEMO_SSHD_CONFIG = """Port 22
Protocol 2
PermitRootLogin no
PasswordAuthentication no
X11Forwarding no
"""


@dataclass(frozen=True)
class CheckResult:
    check_id: str
    status: str  # pass|warn|fail
    message: str
    evidence: dict[str, str] | None = None


class ValidationError(ValueError):
    pass


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _parse_os_release(text: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        result[key.strip()] = value.strip().strip('"')
    if not result:
        raise ValidationError("Unable to parse os-release content")
    return result


def _parse_sshd_config(text: str) -> dict[str, str]:
    kv: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        parts = re.split(r"\s+", line, maxsplit=1)
        if len(parts) != 2:
            continue
        key, value = parts[0].strip(), parts[1].strip()
        kv[key.lower()] = value
    return kv


def _check_sshd(cfg: dict[str, str]) -> list[CheckResult]:
    results: list[CheckResult] = []

    prl = cfg.get("permitrootlogin", "").lower()
    if prl in {"no", "prohibit-password", "without-password"}:
        results.append(CheckResult("ssh.permit_root_login", "pass", "Root login is disabled.", {"PermitRootLogin": prl}))
    elif prl:
        results.append(
            CheckResult(
                "ssh.permit_root_login",
                "fail",
                "Root login is enabled; disable it to reduce blast radius.",
                {"PermitRootLogin": prl},
            )
        )
    else:
        results.append(
            CheckResult(
                "ssh.permit_root_login",
                "warn",
                "PermitRootLogin not explicitly set; define an explicit baseline.",
            )
        )

    pauth = cfg.get("passwordauthentication", "").lower()
    if pauth == "no":
        results.append(
            CheckResult("ssh.password_authentication", "pass", "PasswordAuthentication is disabled.", {"PasswordAuthentication": pauth})
        )
    elif pauth:
        results.append(
            CheckResult(
                "ssh.password_authentication",
                "warn",
                "PasswordAuthentication is enabled; consider disabling and using keys + MFA.",
                {"PasswordAuthentication": pauth},
            )
        )
    else:
        results.append(
            CheckResult(
                "ssh.password_authentication",
                "warn",
                "PasswordAuthentication not explicitly set; define an explicit baseline.",
            )
        )

    x11 = cfg.get("x11forwarding", "").lower()
    if x11 == "no":
        results.append(CheckResult("ssh.x11_forwarding", "pass", "X11Forwarding is disabled.", {"X11Forwarding": x11}))
    elif x11:
        results.append(CheckResult("ssh.x11_forwarding", "warn", "Consider disabling X11Forwarding on servers.", {"X11Forwarding": x11}))
    else:
        results.append(CheckResult("ssh.x11_forwarding", "warn", "X11Forwarding not explicitly set; define an explicit baseline."))

    return results


def _system_facts(mode: str) -> dict[str, str]:
    facts = {
        "mode": mode,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "kernel_release": platform.release(),
        "hostname": platform.node(),
        "uid": str(os.getuid()),
    }
    return facts


def run_audit(*, mode: str, ssh_config_path: Path | None) -> dict[str, object]:
    if mode not in {"demo", "production"}:
        raise ValidationError("mode must be demo or production")

    if mode == "demo":
        os_release_text = DEMO_OS_RELEASE
        sshd_text = DEMO_SSHD_CONFIG
        ssh_source = "built-in fixture"
    else:
        os_release_path = Path("/etc/os-release")
        if not os_release_path.exists():
            raise ValidationError("Missing /etc/os-release. Run on a Linux host or use demo mode.")
        os_release_text = _read_text(os_release_path)

        default_ssh = Path("/etc/ssh/sshd_config")
        effective_ssh = ssh_config_path or default_ssh
        if not effective_ssh.exists():
            raise ValidationError(
                "Missing SSH config file.\n"
                f"- Tried: {effective_ssh}\n"
                "Set SSH_CONFIG_PATH to a valid sshd_config path or run demo mode.\n"
                "Example:\n"
                "  SSH_CONFIG_PATH=/etc/ssh/sshd_config TEST_MODE=production PRODUCTION_TESTS_CONFIRM=1 python3 tests/run_tests.py"
            )
        sshd_text = _read_text(effective_ssh)
        ssh_source = str(effective_ssh)

    os_release = _parse_os_release(os_release_text)
    sshd_cfg = _parse_sshd_config(sshd_text)

    checks = _check_sshd(sshd_cfg)
    report = {
        "collected_at": _now_iso(),
        "facts": _system_facts(mode),
        "os_release": os_release,
        "inputs": {"sshd_config_source": ssh_source},
        "checks": [c.__dict__ for c in checks],
    }
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a Linux baseline governance report.")
    parser.add_argument("--mode", choices=["demo", "production"], default="demo", help="Execution mode.")
    parser.add_argument(
        "--out",
        default="artifacts/linux_baseline_report.json",
        help="Output path for the JSON report.",
    )
    parser.add_argument(
        "--ssh-config-path",
        default=None,
        help="Optional path to sshd_config (production mode). Defaults to /etc/ssh/sshd_config.",
    )
    args = parser.parse_args(argv)

    ssh_config_path = Path(args.ssh_config_path) if args.ssh_config_path else None
    report = run_audit(mode=args.mode, ssh_config_path=ssh_config_path)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
