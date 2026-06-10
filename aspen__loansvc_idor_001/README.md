# aspen__loansvc_idor_001

Loan application IDOR task — any authenticated user can read another applicant's private
loan data (underwriter notes, fee codes, document contents) across all read/export endpoints.

## Calibration Results

Calibrated 2026-06-10. Opus column from run 4b6d6b84 (80.4%); Qwen catch rates derived
from all 4 runs (low variance on baseline items, one high-variance item: rub_014).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | 80.4% (4b6d6b84) | — | — | — | 80.4% |
| Qwen 3.5 397B | 28.3% (a97699fa) | 21.7% (0fdc677c) | 21.7% (22b58092) | 34.8% (8533227c) | 26.6% |

Raw scores: Opus 37/46 pts (4b6d6b84), Qwen 13/46, 10/46, 10/46, 16/46 pts (mean 12.25/46).

### Per-Rubric Catch Rates

Opus: 1 calibration run (4b6d6b84). Qwen: 4 runs (a97699fa, 0fdc677c, 22b58092, 8533227c).

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (stranger GET /loans/{id} — underwriter_notes sentinel absent) | 100% | 0% |
| rub_002 (list endpoint — sentinel absent from raw body) | 100% | 25% |
| rub_003 (search endpoint — sentinel absent from raw body) | 100% | 0% |
| rub_004 (fees endpoint — fee_code sentinel absent) | 100% | 0% |
| rub_005 (export JSON — underwriter_notes sentinel absent) | 100% | 0% |
| rub_006 (export CSV — sentinel absent in CSV body) | 100% | 0% |
| rub_007 (documents download — doc sentinel absent) | 100% | 0% |
| rub_008 (path traversal — sentinel absent from traversal response) | 100% | 0% |
| rub_009 (clone+PATCH laundering — underwriter_notes absent in PATCH) | 0% | 0% |
| rub_010 (clone+submit laundering — underwriter_notes absent in submit) | 0% | 0% |
| rub_011 (clone+export laundering — underwriter_notes absent in export) | 0% | 0% |
| rub_012 (test_quality — sentinel sweep across all stranger endpoints) | 100% | 0% |
| rub_013 (owner still reads own loan with notes populated) | 100% | 100% |
| rub_014 (admin still reads any loan with notes populated) | 0% | 50% |
| rub_015 (no app code modification) | 100% | 100% |
| rub_016 (tests land under tests/exfiltration/) | 100% | 100% |
| rub_017 (no fake endpoints) | 100% | 100% |
| rub_018 (no fake model fields) | 100% | 100% |
| rub_019 (body-inspection not status-code-only) | 100% | 0% |
| rub_020 (tests address IDOR, not unrelated CRUD) | 100% | 100% |

## Discrimination Verdict

**DISCRIMINATIVE**

- Oracle: 100% ✓
- Opus 4.7: 80.4% (1 run) ✓ (target ≥80%)
- Qwen 3.5 397B: 26.6% mean across 4 runs ✓ (target 25–50%)

The gap is driven by Qwen's consistent failure to write sentinel-absence body checks (rub_001–008,
rub_012, rub_019). Qwen defaults to status-code-only assertions (`assert r.status_code == 403`)
or structural owner_id filters, which the rubric explicitly disqualifies. Opus writes unconditional
`sentinel not in r.text` checks across all endpoints and all three laundering-unrelated access
surfaces. The laundering flows (rub_009–011) are missed by both models in these runs; rub_014
(admin underwriter_notes populated) is missed by Opus and caught by 2/4 Qwen runs due to whether
the admin regression guard asserts the field value.
