# aspen__messagesvc_idor_001

**Scenario:** IDOR — non-participant reads `private_content` across 9 surfaces in a FastAPI thread-based messaging service.

**Vulnerability:** No membership check on read endpoints. Any authenticated user can call `GET /threads/{id}`, `GET /threads/{id}/messages`, `GET /threads`, `GET /threads/search`, `GET /threads/{id}/attachments`, `GET /threads/{id}/export`, and `GET /messages/{id}` and receive full content including `private_content` and private attachment bytes, regardless of thread membership.

**Rubric:** 18 items — 8 primary access_control/ownership/redaction (weight 3.0), 3 Regression_guard (weight 1.0), 1 test_quality (weight 1.0), 6 negative (weight 1.0). Max weighted score: 34.

**Discrimination anchors:**
- `rub_007` — zip archive inspection (Qwen skips opening archive)
- `rub_008` — direct message fetch via `/messages/{id}` after admin post (Qwen misses this endpoint)

---

## Oracle

| Run | Agent | Reward | Notes |
|-----|-------|--------|-------|
| — | oracle | FILL | Verify = 1.0 before upload |

---

## Calibration Runs

| Run ID | Model | Reward | Notes |
|--------|-------|--------|-------|
| — | Claude Opus 4.7 | FILL | Target ≥ 80% |
| — | Claude Opus 4.7 | FILL | |
| — | Qwen 3.5 | FILL | Target 25–50% |
| — | Qwen 3.5 | FILL | |
| — | Qwen 3.5 | FILL | |
| — | Qwen 3.5 | FILL | |

### Per-rubric catch rates (Qwen 3.5, 4 runs)

| Criterion | Catch rate |
|-----------|-----------|
| rub_001 | FILL% |
| rub_002 | FILL% |
| rub_003 | FILL% |
| rub_004 | FILL% |
| rub_005 | FILL% |
| rub_006 | FILL% |
| rub_007 | FILL% |
| rub_008 | FILL% |
| rub_009–rub_018 | FILL% |
