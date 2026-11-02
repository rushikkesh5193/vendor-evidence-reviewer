"""Synthetic vendor evidence with problems injected on purpose.

    python3 -m tools.gen_sample examples/sample_evidence.json
"""
import json
import sys

SVC = ["Platform", "API"]


def soc2(**kw):
    d = {"type": "soc2", "report_type": "type2", "period_start": "2025-10-01", "period_end": "2026-09-30", "opinion": "unqualified",
         "exceptions": 0, "scope_services": SVC, "bridge_letter_date": "2026-10-10"}
    d.update(kw)
    return d


def iso(**kw):
    d = {"type": "iso27001", "cert_expiry": "2028-03-01", "scope_services": SVC, "accredited_body": True}
    d.update(kw)
    return d


def pentest(**kw):
    d = {"type": "pentest", "test_date": "2026-06-01", "scope_services": SVC,
         "findings": [{"id": "F-1", "severity": "high", "status": "closed", "retest_date": "2026-07-01"}, {"id": "F-2", "severity": "low", "status": "open"}]}
    d.update(kw)
    return d


def bcp(**kw):
    d = {"type": "bcp_dr", "plan_date": "2026-03-01", "last_test_date": "2026-05-15", "rto_target_hours": 8, "rto_achieved_hours": 6, "result": "pass"}
    d.update(kw)
    return d


def clean(i, tier=1):
    ev = {1: [soc2(), pentest(), bcp()], 2: [soc2(), bcp()], 3: [iso()], 4: []}[tier]
    return {"id": f"V{i:03d}", "name": f"Vendor {i:03d}", "tier": tier, "services_used": list(SVC), "evidence": ev}


def build():
    v = [clean(i, 1 + i % 4) for i in range(11, 31)]
    def mk(i, tier, ev, svc=None):
        d = clean(i, tier)
        d["evidence"] = ev
        if svc:
            d["services_used"] = svc
        return d
    inj = [
        mk(1, 1, [soc2(), pentest()]),                                                            # no BCP/DR evidence
        mk(2, 1, [soc2(report_type="type1", period_start="2026-08-01", period_end="2026-09-30"), pentest(), bcp()]),   # Type 1 only, and a short period
        mk(3, 2, [soc2(period_start="2024-08-01", period_end="2025-07-31", bridge_letter_date=None), bcp()]),        # stale
        mk(4, 1, [soc2(opinion="qualified", exceptions=3), pentest(), bcp()]),                    # qualified opinion and exceptions
        mk(5, 1, [soc2(scope_services=["Platform"]), pentest(), bcp()]),                          # API outside SOC 2 scope
        mk(6, 3, [iso(cert_expiry="2026-09-30")]),                                                # ISO expired
        mk(7, 3, [iso(cert_expiry="2026-12-15", accredited_body=False)]),                         # expiring and unaccredited body
        mk(8, 1, [soc2(), pentest(findings=[{"id": "F-9", "severity": "critical", "status": "open"},
                                            {"id": "F-3", "severity": "high", "status": "closed"}]), bcp()]),   # open critical, closed high with no retest
        mk(9, 1, [soc2(), pentest(test_date="2025-05-01"), bcp()]),                                # stale pen test
        mk(10, 1, [soc2(bridge_letter_date=None, period_end="2026-06-30", period_start="2025-07-01"), pentest(), bcp(last_test_date="2025-06-01", rto_achieved_hours=12)]),   # no bridge, stale and failed DR test
    ]
    return {"_note": "Synthetic data. Problems are injected on purpose.", "vendors": inj + v}


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "examples/sample_evidence.json"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(build(), fh, indent=2)
        fh.write("\n")
