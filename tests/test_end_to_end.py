import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from evrev import analyse, load
from evrev.report import issues_csv, questions_md, to_markdown

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "examples" / "sample_evidence.json"
AS_OF = date(2026, 10, 23)
EXPECTED = {
    ("V001", "EVIDENCE_MISSING"), ("V002", "SOC2_TYPE1_ONLY"), ("V002", "SOC2_PERIOD_SHORT"), ("V003", "SOC2_STALE"),
    ("V004", "SOC2_OPINION_NOT_CLEAN"), ("V004", "SOC2_EXCEPTIONS"), ("V005", "SCOPE_GAP"), ("V006", "ISO_EXPIRED"),
    ("V007", "ISO_EXPIRING"), ("V007", "ISO_BODY_NOT_ACCREDITED"), ("V008", "PENTEST_OPEN_FINDING"), ("V008", "PENTEST_UNVERIFIED"),
    ("V009", "PENTEST_STALE"), ("V010", "SOC2_BRIDGE_MISSING"), ("V010", "DR_TEST_STALE"), ("V010", "DR_TEST_FAILED"),
}


class TestSample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.res = analyse(load(SAMPLE), as_of=AS_OF)

    def test_finds_exactly_the_injected_problems(self):
        got = {(i["vendor"], i["check"]) for i in self.res["issues"]}
        self.assertEqual(got - EXPECTED, set(), "false positives")
        self.assertEqual(EXPECTED - got, set(), "missed")

    def test_clean_vendors_are_accepted(self):
        for vid, verdict in self.res["verdicts"].items():
            if vid > "V010":
                self.assertEqual(verdict, "accept", vid)

    def test_verdicts(self):
        v = self.res["verdicts"]
        self.assertEqual(v["V008"], "follow_up_required")
        self.assertEqual(v["V002"], "accept_with_conditions")

    def test_outputs(self):
        self.assertEqual(len(list(csv.reader(io.StringIO(issues_csv(self.res))))), len(EXPECTED) + 1)
        q = questions_md(self.res)
        self.assertIn("## Vendor 008", q)
        self.assertIn("F-9", q)
        self.assertIn("Follow-up required", to_markdown(self.res))


class TestCli(unittest.TestCase):
    def run_cli(self, *a):
        return subprocess.run([sys.executable, "-m", "evrev", *a], cwd=ROOT, capture_output=True, text=True)

    def test_writes_files(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_cli(str(SAMPLE), "--as-of", "2026-10-23", "--out-dir", d)
            self.assertEqual(r.returncode, 0, r.stderr)
            for f in ("report.md", "report.json", "issues.csv", "vendor_questions.md"):
                self.assertTrue((Path(d) / f).is_file(), f)
            self.assertEqual(len(json.loads((Path(d) / "report.json").read_text())["issues"]), len(EXPECTED))

    def test_exit_codes(self):
        self.assertEqual(self.run_cli(str(SAMPLE), "--as-of", "2026-10-23", "--fail-on", "critical").returncode, 1)
        self.assertEqual(self.run_cli("nope.json").returncode, 2)
        self.assertEqual(self.run_cli(str(SAMPLE), "--as-of", "x").returncode, 2)


if __name__ == "__main__":
    unittest.main()
