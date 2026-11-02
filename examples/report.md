# Vendor assurance evidence review

As of 2026-10-23. 30 vendors reviewed, 16 issues.

| Vendor | Verdict | Issues |
|---|---|---|
| Vendor 001 (`V001`) | Follow-up required | 1 |
| Vendor 002 (`V002`) | Accept with conditions | 2 |
| Vendor 003 (`V003`) | Follow-up required | 1 |
| Vendor 004 (`V004`) | Follow-up required | 2 |
| Vendor 005 (`V005`) | Follow-up required | 1 |
| Vendor 006 (`V006`) | Follow-up required | 1 |
| Vendor 007 (`V007`) | Accept with conditions | 2 |
| Vendor 008 (`V008`) | Follow-up required | 2 |
| Vendor 009 (`V009`) | Follow-up required | 1 |
| Vendor 010 (`V010`) | Follow-up required | 3 |
| Vendor 011 (`V011`) | Accept | 0 |
| Vendor 012 (`V012`) | Accept | 0 |
| Vendor 013 (`V013`) | Accept | 0 |
| Vendor 014 (`V014`) | Accept | 0 |
| Vendor 015 (`V015`) | Accept | 0 |
| Vendor 016 (`V016`) | Accept | 0 |
| Vendor 017 (`V017`) | Accept | 0 |
| Vendor 018 (`V018`) | Accept | 0 |
| Vendor 019 (`V019`) | Accept | 0 |
| Vendor 020 (`V020`) | Accept | 0 |
| Vendor 021 (`V021`) | Accept | 0 |
| Vendor 022 (`V022`) | Accept | 0 |
| Vendor 023 (`V023`) | Accept | 0 |
| Vendor 024 (`V024`) | Accept | 0 |
| Vendor 025 (`V025`) | Accept | 0 |
| Vendor 026 (`V026`) | Accept | 0 |
| Vendor 027 (`V027`) | Accept | 0 |
| Vendor 028 (`V028`) | Accept | 0 |
| Vendor 029 (`V029`) | Accept | 0 |
| Vendor 030 (`V030`) | Accept | 0 |

## Issues

### Critical (1)

- **PENTEST_OPEN_FINDING** Vendor 008 (`V008`): Critical finding F-9 is still open.

### High (8)

- **EVIDENCE_MISSING** Vendor 001 (`V001`): No BCP/DR evidence on file.
- **SOC2_STALE** Vendor 003 (`V003`): Report period ended 2025-07-31, over 12 months ago.
- **SOC2_OPINION_NOT_CLEAN** Vendor 004 (`V004`): Auditor opinion is qualified.
- **SCOPE_GAP** Vendor 005 (`V005`): Services we use are outside the assurance scope: API.
- **ISO_EXPIRED** Vendor 006 (`V006`): Certificate expired 2026-09-30.
- **PENTEST_STALE** Vendor 009 (`V009`): Last penetration test 2025-05-01.
- **DR_TEST_FAILED** Vendor 010 (`V010`): Last DR test missed its target (achieved 12h, target 8h).
- **DR_TEST_STALE** Vendor 010 (`V010`): Last DR test 2025-06-01.

### Medium (6)

- **SOC2_PERIOD_SHORT** Vendor 002 (`V002`): Observation period 2026-08-01 to 2026-09-30 is under 6 months.
- **SOC2_TYPE1_ONLY** Vendor 002 (`V002`): Only a point-in-time Type 1 report; Type 2 is expected for this tier.
- **SOC2_EXCEPTIONS** Vendor 004 (`V004`): 3 control exception(s) reported.
- **ISO_BODY_NOT_ACCREDITED** Vendor 007 (`V007`): Certification body is not accredited.
- **ISO_EXPIRING** Vendor 007 (`V007`): Certificate expires 2026-12-15.
- **PENTEST_UNVERIFIED** Vendor 008 (`V008`): High finding F-3 was closed without a retest.

### Low (1)

- **SOC2_BRIDGE_MISSING** Vendor 010 (`V010`): Period ended 2026-06-30 and no bridge letter covers the gap since.

