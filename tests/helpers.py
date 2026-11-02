from datetime import date

from evrev import analyse, load_config, validate

AS_OF = date(2026, 10, 23)
CFG = load_config()
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


def pentest(findings=None, **kw):
    d = {"type": "pentest", "test_date": "2026-06-01", "scope_services": SVC, "findings": findings or []}
    d.update(kw)
    return d


def bcp(**kw):
    d = {"type": "bcp_dr", "plan_date": "2026-03-01", "last_test_date": "2026-05-15", "rto_target_hours": 8, "rto_achieved_hours": 6, "result": "pass"}
    d.update(kw)
    return d


def vendor(tier=1, evidence=None, **kw):
    d = {"id": "T1", "name": "Test", "tier": tier, "services_used": list(SVC),
         "evidence": [soc2(), pentest(), bcp()] if evidence is None else evidence}
    d.update(kw)
    return d


def run(**kw):
    return analyse(validate([vendor(**kw)]), CFG, AS_OF)


def checks(**kw):
    return {i["check"] for i in run(**kw)["issues"]}
