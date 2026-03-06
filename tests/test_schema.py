import json
import tempfile
import unittest
from pathlib import Path

from pipelines.pipeline import ValidationError, run_audit


class TestBaselineAudit(unittest.TestCase):
    def test_demo_audit_produces_report_with_checks(self) -> None:
        report = run_audit(mode="demo", ssh_config_path=None)
        self.assertIn("checks", report)
        checks = report["checks"]
        self.assertIsInstance(checks, list)
        self.assertGreaterEqual(len(checks), 3)

    def test_production_mode_requires_linux_os_release(self) -> None:
        with self.assertRaises(ValidationError):
            run_audit(mode="invalid", ssh_config_path=None)  # type: ignore[arg-type]

    def test_report_is_json_serializable(self) -> None:
        report = run_audit(mode="demo", ssh_config_path=None)
        with tempfile.TemporaryDirectory() as tmpdir:
            out = Path(tmpdir) / "report.json"
            out.write_text(json.dumps(report), encoding="utf-8")
            self.assertTrue(out.exists())


if __name__ == "__main__":
    unittest.main()
