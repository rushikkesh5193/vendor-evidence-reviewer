import csv
import io
import json

LABEL = {"accept": "Accept", "accept_with_conditions": "Accept with conditions", "follow_up_required": "Follow-up required"}


def issues_csv(res):
    b = io.StringIO()
    w = csv.writer(b, lineterminator="\n")
    w.writerow(["severity", "vendor", "name", "check", "detail", "question"])
    w.writerows([[i["severity"], i["vendor"], i["name"], i["check"], i["detail"], i["question"]] for i in res["issues"]])
    return b.getvalue()


def to_json(res):
    return json.dumps(res, indent=2)


def to_markdown(res):
    v = res["verdicts"]
    L = ["# Vendor assurance evidence review", "", f"As of {res['as_of']}. {len(v)} vendors reviewed, {len(res['issues'])} issues.", "",
         "| Vendor | Verdict | Issues |", "|---|---|---|"]
    for vid in sorted(v):
        n = sum(i["vendor"] == vid for i in res["issues"])
        L.append(f"| {res['names'][vid]} (`{vid}`) | {LABEL[v[vid]]} | {n} |")
    L += ["", "## Issues", ""]
    for sev in ("critical", "high", "medium", "low"):
        rows = [i for i in res["issues"] if i["severity"] == sev]
        if rows:
            L += [f"### {sev.title()} ({len(rows)})", ""]
            L += [f"- **{i['check']}** {i['name']} (`{i['vendor']}`): {i['detail']}" for i in rows] + [""]
    return "\n".join(L) + "\n"


def questions_md(res):
    L = ["# Follow-up questions for vendors", ""]
    for vid in sorted({i["vendor"] for i in res["issues"]}):
        rows = [i for i in res["issues"] if i["vendor"] == vid]
        L += [f"## {res['names'][vid]} (`{vid}`)", ""] + [f"{n}. {i['question']}" for n, i in enumerate(rows, 1)] + [""]
    return "\n".join(L) + "\n"
