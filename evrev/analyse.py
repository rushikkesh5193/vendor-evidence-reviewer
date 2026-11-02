import json
from pathlib import Path

from .models import SEVERITIES, add_months

SEV = {s: i for i, s in enumerate(SEVERITIES)}


def load_config(path=None):
    return json.loads((Path(path) if path else Path(__file__).with_name("config.json")).read_text(encoding="utf-8"))


def _i(sev, v, check, detail, question):
    return {"severity": sev, "vendor": v["id"], "name": v["name"], "check": check, "detail": detail, "question": question}


def _by_tier(tier, high="high"):
    return {1: high, 2: high, 3: "medium", 4: "low"}[tier]


def _older(d, months, as_of):
    return add_months(d, months) < as_of


def analyse(vendors, cfg=None, as_of=None):
    cfg = cfg or load_config()
    issues, verdicts = [], {}
    for v in vendors:
        t = v["tier"]
        ev = {k: [e for e in v["evidence"] if e["type"] == k] for k in ("soc2", "iso27001", "pentest", "bcp_dr")}
        found = []
        need = cfg["required_evidence"][str(t)]
        if "assurance" in need and not ev["soc2"] and not ev["iso27001"]:
            found.append(_i(_by_tier(t), v, "EVIDENCE_MISSING", "No SOC 2 report or ISO 27001 certificate on file.", "Please provide a current SOC 2 Type 2 report or ISO 27001 certificate."))
        if "pentest" in need and not ev["pentest"]:
            found.append(_i("high", v, "EVIDENCE_MISSING", "No penetration test report on file.", "Please provide your latest independent penetration test summary and remediation status."))
        if "bcp_dr" in need and not ev["bcp_dr"]:
            found.append(_i("high", v, "EVIDENCE_MISSING", "No BCP/DR evidence on file.", "Please provide your BCP/DR plan summary and latest test results."))

        covered = set()
        for e in ev["soc2"]:
            covered |= set(e["scope_services"])
            if e["report_type"] == "type1" and t in cfg["type2_required_tiers"]:
                found.append(_i("medium", v, "SOC2_TYPE1_ONLY", "Only a point-in-time Type 1 report; Type 2 is expected for this tier.", "Please share your SOC 2 Type 2 report, or the date it will be available."))
            if _older(e["period_end"], cfg["soc2_max_age_months"], as_of):
                found.append(_i(_by_tier(t), v, "SOC2_STALE", f"Report period ended {e['period_end']}, over {cfg['soc2_max_age_months']} months ago.", "Please provide your most recent SOC 2 report."))
            elif _older(e["period_end"], cfg["soc2_bridge_after_months"], as_of) and not e["bridge_letter_date"]:
                found.append(_i("low", v, "SOC2_BRIDGE_MISSING", f"Period ended {e['period_end']} and no bridge letter covers the gap since.", "Please provide a bridge (gap) letter confirming no material control changes since the period end."))
            if add_months(e["period_start"], cfg["soc2_min_period_months"]) > e["period_end"]:
                found.append(_i("medium", v, "SOC2_PERIOD_SHORT", f"Observation period {e['period_start']} to {e['period_end']} is under {cfg['soc2_min_period_months']} months.", "Why is the observation period short? When will a longer period report be issued?"))
            if e["opinion"] != "unqualified":
                found.append(_i("high", v, "SOC2_OPINION_NOT_CLEAN", f"Auditor opinion is {e['opinion']}.", "Please explain the basis for the modified opinion and your remediation plan."))
            if e["exceptions"] > 0:
                found.append(_i("medium", v, "SOC2_EXCEPTIONS", f"{e['exceptions']} control exception(s) reported.", "Please explain each exception, its impact on our services and the remediation."))
        for e in ev["iso27001"]:
            covered |= set(e["scope_services"])
            if e["cert_expiry"] < as_of:
                found.append(_i("high", v, "ISO_EXPIRED", f"Certificate expired {e['cert_expiry']}.", "Please provide the renewed certificate."))
            elif (e["cert_expiry"] - as_of).days <= cfg["iso_expiring_days"]:
                found.append(_i("medium", v, "ISO_EXPIRING", f"Certificate expires {e['cert_expiry']}.", "Please confirm the date of your recertification audit."))
            if e.get("accredited_body") is False:
                found.append(_i("medium", v, "ISO_BODY_NOT_ACCREDITED", "Certification body is not accredited.", "Please confirm the accreditation of your certification body."))
        if (ev["soc2"] or ev["iso27001"]) and v["services_used"]:
            gap = [s for s in v["services_used"] if s not in covered]
            if gap:
                found.append(_i(_by_tier(t), v, "SCOPE_GAP", f"Services we use are outside the assurance scope: {', '.join(gap)}.", f"Is {', '.join(gap)} covered by your SOC 2 or ISO 27001 scope? If not, what other assurance exists?"))

        for e in ev["pentest"]:
            if _older(e["test_date"], cfg["pentest_max_age_months"], as_of):
                found.append(_i(_by_tier(t), v, "PENTEST_STALE", f"Last penetration test {e['test_date']}.", "Please provide a penetration test from the last 12 months."))
            gap = [s for s in v["services_used"] if s not in e["scope_services"]]
            if gap and v["services_used"]:
                found.append(_i("medium", v, "PENTEST_SCOPE_GAP", f"Penetration test did not cover: {', '.join(gap)}.", f"Please confirm whether {', '.join(gap)} has been penetration tested."))
            for f in e["findings"]:
                if f["severity"] in ("critical", "high") and f["status"] == "open":
                    found.append(_i(f["severity"], v, "PENTEST_OPEN_FINDING", f"{f['severity'].title()} finding {f['id']} is still open.", f"What is the remediation date for finding {f['id']}?"))
                elif f["severity"] in ("critical", "high") and f["status"] == "closed" and not f["retest_date"]:
                    found.append(_i("medium", v, "PENTEST_UNVERIFIED", f"{f['severity'].title()} finding {f['id']} was closed without a retest.", f"Please provide retest evidence for finding {f['id']}."))

        for e in ev["bcp_dr"]:
            if e["last_test_date"] is None:
                found.append(_i(_by_tier(t), v, "DR_NOT_TESTED", "No DR test recorded.", "Please provide the date and results of your most recent DR test."))
            else:
                if _older(e["last_test_date"], cfg["dr_test_max_age_months"], as_of):
                    found.append(_i(_by_tier(t, "high"), v, "DR_TEST_STALE", f"Last DR test {e['last_test_date']}.", "Please provide a DR test from the last 12 months."))
                ach, tgt = e.get("rto_achieved_hours"), e.get("rto_target_hours")
                if e.get("result") == "fail" or (ach is not None and tgt is not None and ach > tgt):
                    found.append(_i("high", v, "DR_TEST_FAILED", f"Last DR test missed its target (achieved {ach}h, target {tgt}h).", "What corrective actions followed the failed DR test, and when was it re-run?"))
            if e["plan_date"] is None or _older(e["plan_date"], cfg["bcp_plan_max_age_months"], as_of):
                found.append(_i("low", v, "BCP_PLAN_STALE", f"BCP/DR plan last updated {e['plan_date'] or 'never'}.", "Please provide the current approved BCP/DR plan."))

        issues += found
        worst = min((SEV[i["severity"]] for i in found), default=None)
        verdicts[v["id"]] = "accept" if worst is None else ("follow_up_required" if worst <= 1 else "accept_with_conditions")
    issues.sort(key=lambda i: (SEV[i["severity"]], i["vendor"], i["check"]))
    return {"as_of": str(as_of), "issues": issues, "verdicts": verdicts,
            "names": {v["id"]: v["name"] for v in vendors}}
