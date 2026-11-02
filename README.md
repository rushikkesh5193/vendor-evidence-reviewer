# vendor-evidence-reviewer

A small Python tool that reviews the **assurance evidence** a vendor has given you (SOC 2 reports, ISO 27001 certificates, penetration test results and BCP/DR evidence) and tells you what is missing, out of date, out of scope or unresolved. For each vendor it gives a verdict and writes the follow-up questions to send them.

Python standard library only (tested on Python 3.13).

> **Data note.** `examples/sample_evidence.json` is **synthetic**. Ten of the 30 vendors have evidence problems injected on purpose and the tests check the tool finds exactly those. Nothing here comes from a real organisation.

## What it does and does not do

It checks **recorded facts about the evidence**: dates, scope, opinion type, exception counts, open findings. It does **not** read the PDFs. A person still reads the report; this tool makes sure the reviewer starts from the right questions and nothing is missed.

## Quick start

```bash
python3 -m evrev examples/sample_evidence.json --as-of 2026-10-23 --out-dir out   # report.md, report.json, issues.csv, vendor_questions.md
python3 -m evrev examples/sample_evidence.json --fail-on high                     # exit 1 on any high or critical issue
python3 -m unittest discover -s tests                                             # 29 tests
bash scripts/run_demo.sh                                                          # regenerate data, report and tests
```

## Checks

| Evidence | Checks |
|---|---|
| Required by tier | `EVIDENCE_MISSING`: Tier 1 needs SOC 2 or ISO 27001, a pen test and BCP/DR evidence; Tier 2 assurance and BCP/DR; Tier 3 assurance; Tier 4 none |
| SOC 2 | `SOC2_TYPE1_ONLY` (Tier 1-2), `SOC2_STALE` (period ended over 12 months ago), `SOC2_BRIDGE_MISSING` (over 3 months since period end, no bridge letter), `SOC2_PERIOD_SHORT` (under 6 months), `SOC2_OPINION_NOT_CLEAN`, `SOC2_EXCEPTIONS` |
| SOC 2 / ISO scope | `SCOPE_GAP`: services you use that no report or certificate covers (names them) |
| ISO 27001 | `ISO_EXPIRED`, `ISO_EXPIRING` (90 days), `ISO_BODY_NOT_ACCREDITED` |
| Pen test | `PENTEST_STALE`, `PENTEST_SCOPE_GAP`, `PENTEST_OPEN_FINDING` (critical or high still open), `PENTEST_UNVERIFIED` (critical or high closed with no retest) |
| BCP/DR | `DR_NOT_TESTED`, `DR_TEST_STALE`, `DR_TEST_FAILED` (failed, or achieved RTO above target), `BCP_PLAN_STALE` |

**Verdicts:** any critical or high issue gives *Follow-up required*; only medium or low gives *Accept with conditions*; none gives *Accept*. Every issue comes with a ready-to-send question in `vendor_questions.md`.

Thresholds and tier requirements are in `evrev/config.json`.

## Limitations

- **It trusts what you record.** If someone types the wrong period end date, the tool will be wrong with confidence.
- **It does not judge quality.** A clean SOC 2 opinion can still cover the wrong systems or wrong trust criteria; scope matching only compares service names you enter.
- **Exceptions are counted, not read.** Whether an exception matters needs a human.
- **The tier requirements and age limits are illustrative defaults**, not a standard. Set your own policy in the config.
- No persistence, UI or authentication. It reads JSON and writes reports.

## Layout

```
evrev/     models.py  analyse.py  report.py  config.json  __main__.py
tools/     gen_sample.py     synthetic data generator
tests/     29 tests          incl. an exact-match end-to-end test
examples/  sample_evidence.json  report.md  report.json  issues.csv  vendor_questions.md
scripts/   run_demo.sh
```
