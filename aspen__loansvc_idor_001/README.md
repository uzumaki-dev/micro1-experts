# aspen__loansvc_idor_001

Loan application IDOR task — any authenticated user can read another applicant's private
loan data (underwriter notes, fee codes, document contents) across all read/export endpoints.

## Calibration Results

Calibrated YYYY-MM-DD. Opus column from run <id> (<score>%); Qwen catch rates derived
from all 4 runs (<note about variance>).

| Model | Run 1 | Run 2 | Run 3 | Run 4 | Mean |
|-------|-------|-------|-------|-------|------|
| Oracle (solve.sh) | 100% | — | — | — | 100% |
| Claude Opus 4.7 | <score>% (<run_id>) | — | — | — | <score>% |
| Qwen 3.5 397B | <score>% (<run_id>) | <score>% (<run_id>) | <score>% (<run_id>) | <score>% (<run_id>) | <mean>% |

Raw scores: Opus <pts>/45 pts (<run_id>), Qwen <pts>/45 pts (<run_id>).

### Per-Rubric Catch Rates

Opus: 1 calibration run (<run_id>). Qwen: 4 runs.

| Criterion | Opus 4.7 | Qwen 3.5 |
|-----------|----------|----------|
| rub_001 (stranger GET /loans/{id} — underwriter_notes absent) | — | — |
| rub_002 (list endpoint — sentinel absent) | — | — |
| rub_003 (search endpoint — sentinel absent) | — | — |
| rub_004 (fees endpoint — fee_code absent) | — | — |
| rub_005 (export JSON — underwriter_notes absent) | — | — |
| rub_006 (export CSV — sentinel absent) | — | — |
| rub_007 (documents download — doc sentinel absent) | — | — |
| rub_008 (path traversal blocked) | — | — |
| rub_009 (clone+PATCH laundering) | — | — |
| rub_010 (clone+submit laundering) | — | — |
| rub_011 (clone+export laundering) | — | — |
| rub_012 (test_quality sentinel sweep) | — | — |
| rub_013 (owner still reads own loan) | — | — |
| rub_014 (admin still reads any loan) | — | — |
| rub_015 (no app code modification) | — | — |
| rub_016 (tests in right dir) | — | — |
| rub_017 (no fake endpoints) | — | — |
| rub_018 (no fake fields) | — | — |
| rub_019 (body-inspection not status-code-only) | — | — |
| rub_020 (tests address IDOR, not unrelated CRUD) | — | — |

## Discrimination Verdict

**PENDING CALIBRATION**

- Oracle: 100% ✓
- Opus 4.7: <score>% (<N> run(s)) (target ≥80%)
- Qwen 3.5 397B: <mean>% mean across 4 runs (target 25–50%)
