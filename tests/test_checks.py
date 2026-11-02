import unittest

from helpers import bcp, checks, iso, pentest, run, soc2, vendor, SVC
from evrev import validate


class TestBaseline(unittest.TestCase):
    def test_clean_vendor_accepted(self):
        res = run()
        self.assertEqual(res["issues"], [])
        self.assertEqual(res["verdicts"]["T1"], "accept")


class TestRequiredEvidence(unittest.TestCase):
    def test_requirements_follow_tier(self):
        self.assertEqual(len(run(evidence=[])["issues"]), 3)                 # Tier 1 needs assurance, pentest, BCP/DR
        self.assertEqual(len(run(tier=2, evidence=[])["issues"]), 2)
        self.assertEqual(len(run(tier=3, evidence=[])["issues"]), 1)
        self.assertEqual(run(tier=4, evidence=[])["issues"], [])

    def test_iso_alone_satisfies_assurance(self):
        self.assertEqual(checks(tier=3, evidence=[iso()]), set())


class TestSoc2(unittest.TestCase):
    def test_type1_only_flagged_for_top_tiers(self):
        self.assertIn("SOC2_TYPE1_ONLY", checks(evidence=[soc2(report_type="type1"), pentest(), bcp()]))
        self.assertNotIn("SOC2_TYPE1_ONLY", checks(tier=3, evidence=[soc2(report_type="type1")]))

    def test_stale_boundary(self):
        self.assertIn("SOC2_STALE", checks(evidence=[soc2(period_end="2025-10-22", period_start="2024-10-23"), pentest(), bcp()]))
        self.assertNotIn("SOC2_STALE", checks(evidence=[soc2(period_end="2025-10-23", period_start="2024-10-24", bridge_letter_date="2026-10-01"), pentest(), bcp()]))

    def test_bridge_letter_needed_after_three_months(self):
        ev = lambda end, br: [soc2(period_start="2025-07-01", period_end=end, bridge_letter_date=br), pentest(), bcp()]
        self.assertIn("SOC2_BRIDGE_MISSING", checks(evidence=ev("2026-07-22", None)))      # 3 months + 1 day
        self.assertNotIn("SOC2_BRIDGE_MISSING", checks(evidence=ev("2026-07-23", None)))   # exactly 3 months
        self.assertNotIn("SOC2_BRIDGE_MISSING", checks(evidence=ev("2026-07-22", "2026-10-01")))

    def test_short_period(self):
        e = lambda s, en: [soc2(period_start=s, period_end=en), pentest(), bcp()]
        self.assertIn("SOC2_PERIOD_SHORT", checks(evidence=e("2026-04-01", "2026-09-29")))
        self.assertNotIn("SOC2_PERIOD_SHORT", checks(evidence=e("2026-03-31", "2026-09-30")))

    def test_opinion_and_exceptions(self):
        got = checks(evidence=[soc2(opinion="qualified", exceptions=2), pentest(), bcp()])
        self.assertIn("SOC2_OPINION_NOT_CLEAN", got)
        self.assertIn("SOC2_EXCEPTIONS", got)

    def test_scope_gap_names_the_uncovered_service(self):
        i = [x for x in run(evidence=[soc2(scope_services=["Platform"]), pentest(), bcp()])["issues"] if x["check"] == "SCOPE_GAP"]
        self.assertEqual(len(i), 1)
        self.assertIn("API", i[0]["detail"])
        self.assertNotIn("Platform", i[0]["detail"])

    def test_scope_covered_by_either_report(self):
        ev = [soc2(scope_services=["Platform"]), iso(scope_services=["API"]), pentest(), bcp()]
        self.assertNotIn("SCOPE_GAP", checks(evidence=ev))


class TestIso(unittest.TestCase):
    def test_expiry_windows(self):
        self.assertIn("ISO_EXPIRED", checks(tier=3, evidence=[iso(cert_expiry="2026-10-22")]))
        got = checks(tier=3, evidence=[iso(cert_expiry="2026-10-23")])
        self.assertNotIn("ISO_EXPIRED", got)
        self.assertIn("ISO_EXPIRING", got)
        self.assertIn("ISO_EXPIRING", checks(tier=3, evidence=[iso(cert_expiry="2027-01-21")]))      # 90 days
        self.assertNotIn("ISO_EXPIRING", checks(tier=3, evidence=[iso(cert_expiry="2027-01-22")]))    # 91 days

    def test_unaccredited_body(self):
        self.assertIn("ISO_BODY_NOT_ACCREDITED", checks(tier=3, evidence=[iso(accredited_body=False)]))


class TestPentest(unittest.TestCase):
    def ev(self, findings=None, **kw):
        return [soc2(), pentest(findings, **kw), bcp()]

    def test_age_boundary(self):
        self.assertIn("PENTEST_STALE", checks(evidence=self.ev(test_date="2025-10-22")))
        self.assertNotIn("PENTEST_STALE", checks(evidence=self.ev(test_date="2025-10-23")))

    def test_open_high_and_critical_findings(self):
        for sev in ("critical", "high"):
            i = run(evidence=self.ev([{"id": "F", "severity": sev, "status": "open"}]))["issues"]
            self.assertEqual([(x["check"], x["severity"]) for x in i], [("PENTEST_OPEN_FINDING", sev)])
        self.assertEqual(checks(evidence=self.ev([{"id": "F", "severity": "medium", "status": "open"}])), set())

    def test_closed_without_retest(self):
        f = {"id": "F", "severity": "high", "status": "closed"}
        self.assertIn("PENTEST_UNVERIFIED", checks(evidence=self.ev([f])))
        self.assertNotIn("PENTEST_UNVERIFIED", checks(evidence=self.ev([dict(f, retest_date="2026-07-01")])))

    def test_scope_gap(self):
        self.assertIn("PENTEST_SCOPE_GAP", checks(evidence=self.ev(scope_services=["Platform"])))


class TestBcpDr(unittest.TestCase):
    def ev(self, **kw):
        return [soc2(), pentest(), bcp(**kw)]

    def test_never_tested(self):
        self.assertIn("DR_NOT_TESTED", checks(evidence=self.ev(last_test_date=None)))

    def test_stale_boundary(self):
        self.assertIn("DR_TEST_STALE", checks(evidence=self.ev(last_test_date="2025-10-22")))
        self.assertNotIn("DR_TEST_STALE", checks(evidence=self.ev(last_test_date="2025-10-23")))

    def test_failed_by_result_or_by_rto(self):
        self.assertIn("DR_TEST_FAILED", checks(evidence=self.ev(result="fail")))
        self.assertIn("DR_TEST_FAILED", checks(evidence=self.ev(rto_achieved_hours=8.5)))
        self.assertNotIn("DR_TEST_FAILED", checks(evidence=self.ev(rto_achieved_hours=8)))

    def test_plan_age(self):
        self.assertIn("BCP_PLAN_STALE", checks(evidence=self.ev(plan_date="2025-10-22")))
        self.assertIn("BCP_PLAN_STALE", checks(evidence=self.ev(plan_date=None)))


class TestVerdictAndQuestions(unittest.TestCase):
    def test_verdict_follows_worst_severity(self):
        self.assertEqual(run(evidence=[soc2(report_type="type1"), pentest(), bcp()])["verdicts"]["T1"], "accept_with_conditions")
        self.assertEqual(run(evidence=[soc2(opinion="qualified"), pentest(), bcp()])["verdicts"]["T1"], "follow_up_required")
        low_only = [soc2(bridge_letter_date=None, period_end="2026-06-30", period_start="2025-07-01"), pentest(), bcp()]
        self.assertEqual(run(evidence=low_only)["verdicts"]["T1"], "accept_with_conditions")

    def test_every_issue_has_a_question(self):
        res = run(evidence=[soc2(opinion="qualified", exceptions=1), pentest([{"id": "F", "severity": "high", "status": "open"}]), bcp(result="fail")])
        self.assertTrue(res["issues"])
        self.assertTrue(all(i["question"].strip() for i in res["issues"]))


class TestValidation(unittest.TestCase):
    def test_bad_input(self):
        bad = [dict(tier=9), dict(evidence=[{"type": "nonsense"}]), dict(evidence=[soc2(opinion="great")]),
               dict(evidence=[soc2(report_type="type3")]), dict(evidence=[soc2(period_end="2024-01-01")]),
               dict(evidence=[soc2(period_start="31/12/2025")]),
               dict(evidence=[pentest([{"id": "F", "severity": "huge", "status": "open"}])])]
        for kw in bad:
            with self.assertRaises(ValueError, msg=str(kw)):
                validate([vendor(**kw)])
        with self.assertRaises(ValueError):
            validate([vendor(), vendor()])


if __name__ == "__main__":
    unittest.main()
