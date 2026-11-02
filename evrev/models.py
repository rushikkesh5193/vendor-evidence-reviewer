import calendar
import json
from datetime import date

SEVERITIES = ("critical", "high", "medium", "low")
EVIDENCE_TYPES = ("soc2", "iso27001", "pentest", "bcp_dr")


def parse_date(s, field="date"):
    if s in (None, ""):
        return None
    try:
        y, m, d = (int(x) for x in str(s).split("-"))
        return date(y, m, d)
    except (ValueError, TypeError):
        raise ValueError(f"{field}: expected YYYY-MM-DD, got {s!r}")


def add_months(d, n):
    m = d.month - 1 + n
    y, m = d.year + m // 12, m % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


DATE_FIELDS = {"soc2": ("period_start", "period_end", "bridge_letter_date"), "iso27001": ("cert_expiry",),
               "pentest": ("test_date",), "bcp_dr": ("plan_date", "last_test_date")}


def load(path):
    with open(path, encoding="utf-8") as f:
        return validate(json.load(f))


def validate(data):
    rows = data["vendors"] if isinstance(data, dict) else data
    out, seen = [], set()
    for v in rows:
        for k in ("id", "name", "tier"):
            if k not in v:
                raise ValueError(f"vendor {v.get('id', '?')}: missing {k}")
        if v["id"] in seen:
            raise ValueError(f"duplicate vendor id {v['id']}")
        seen.add(v["id"])
        if v["tier"] not in (1, 2, 3, 4):
            raise ValueError(f"vendor {v['id']}: tier must be 1..4, got {v['tier']!r}")
        q = dict(v)
        q["services_used"] = list(v.get("services_used", []))
        ev = []
        for e in v.get("evidence", []):
            if e.get("type") not in EVIDENCE_TYPES:
                raise ValueError(f"vendor {v['id']}: unknown evidence type {e.get('type')!r}")
            x = dict(e)
            for f in DATE_FIELDS[e["type"]]:
                x[f] = parse_date(e.get(f), f"vendor {v['id']} {e['type']}.{f}")
            if e["type"] == "soc2":
                if e.get("report_type") not in ("type1", "type2"):
                    raise ValueError(f"vendor {v['id']}: soc2 report_type must be type1 or type2")
                if e.get("opinion") not in ("unqualified", "qualified", "adverse", "disclaimer"):
                    raise ValueError(f"vendor {v['id']}: soc2 opinion invalid: {e.get('opinion')!r}")
                if x["period_start"] is None or x["period_end"] is None or x["period_end"] < x["period_start"]:
                    raise ValueError(f"vendor {v['id']}: soc2 period is missing or ends before it starts")
                x["exceptions"] = int(e.get("exceptions", 0))
            if e["type"] in ("soc2", "iso27001", "pentest"):
                x["scope_services"] = list(e.get("scope_services", []))
            if e["type"] == "pentest":
                x["findings"] = [dict(f, retest_date=parse_date(f.get("retest_date"), "retest_date")) for f in e.get("findings", [])]
                for f in x["findings"]:
                    if f.get("severity") not in SEVERITIES or f.get("status") not in ("open", "closed"):
                        raise ValueError(f"vendor {v['id']}: pentest finding needs severity and status open/closed")
            ev.append(x)
        q["evidence"] = ev
        out.append(q)
    return out
