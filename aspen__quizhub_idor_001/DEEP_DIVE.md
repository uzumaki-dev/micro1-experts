# Deep Dive — `aspen__quizhub_idor_001`

> **Audience.** A reader who has not seen this repo, this task, or any of our
> internal terminology before. By the end you should be able to say (a) what
> an AI model is graded on here, (b) what the "bug" looks like as code, (c)
> why a real engineer would ship this code, and (d) how to read the
> calibration numbers once they exist.
>
> The companion `README.md` is the team status report — this file is the
> on-ramp for everyone else.

---

## 1. Five-second summary

A frontier AI model is asked to **write a hidden test suite** for a small
FastAPI service that has a real broken-access-control bug. The agent reviews
the code, identifies the leak surface, and authors a test suite that would
catch it — both the leak itself *and* the over-eager fix shapes that would
regress legitimate flows.

An LLM judge then reads the agent's git diff and checks, item by item,
whether the suite covers each of 13 weighted rubric criteria. A perfect suite
= 1.0; missing everything = 0.0.

---

## 2. Why test-authoring is the right shape

The agent's deliverable is **the test suite that codifies the threat model**,
not the fix. That's deliberate:

- **The fix shape is ambiguous in real life.** A correct fix can redact the
  private fields in the response, scrub the persisted row at storage layer,
  or gate the route at auth. None is uniquely "correct." Asking the agent to
  pick a fix and scoring against a hidden test set conflates "which fix did
  you pick?" with "did you understand the threat?"
- **The test suite is unambiguous.** A well-written suite catches the leak
  *regardless of which fix shape the implementer chooses*, and asserts the
  legitimate flows still work afterward. It codifies a **dual contract**:
  "leak must be closed" AND "legitimate student + instructor flows must still
  work."
- **This makes the task pure threat-model induction.** The agent is graded on
  whether it can articulate what an attacker can exploit and what an
  over-eager fix could regress — both halves at once.

---

## 3. The setup — what the agent sees

The agent boots into a small FastAPI service called `quizhub` mounted at
`/repo`. It is a stand-in for an online assessment platform's quiz / attempt /
resource API, deliberately compact (~410 LOC) so the threat model is
enumerable.

Three roles, resolved from bearer tokens in `auth.py`:

- **instructor** (token `instructor-key`) — quiz author; full read/write.
- **alice** (token `student-key`) — student; can take quizzes, duplicate
  quizzes into a practice library, share/export her own copies.
- **bob** (token `student2-key`) — second student; used for cross-author
  privacy testing.

A **quiz** carries public fields (`title`, `questions`, a public handout
file) and a private **`answer_bundle`**: `answer_key_b64`, `solution_pdf_b64`,
`grader_notes_b64`, and `hidden_resource_files` (filenames only instructors
should reach). Eight endpoints across three router files leak it:

| Endpoint | Intended use | Bug |
| --- | --- | --- |
| `GET /quizzes/{id}` | Read quiz metadata | Returns full row including private `answer_bundle` |
| `GET /quiz-bank` (list) | Browse the quiz bank | Returns full rows verbatim |
| `GET /quizzes/{id}/resources/{path}` | Download a public resource | Naive `os.path.join` reaches hidden files and the `.key/` dir |
| `GET /quizzes/{id}/key-file/{path}` | Instructor key-file access | Public-by-default route serves `.key/answer_key.txt` |
| `POST /quizzes/{id}/duplicate` | Duplicate a quiz (student) | Deep-copies the private `answer_bundle` into the clone |
| `PATCH /quizzes/{id}` | Rename a quiz | Returns the full updated row (laundering surface) |
| `POST /quizzes/{id}/share` | Generate a share payload | Inlines the full `answer_bundle` into the response |
| `GET /quizzes/{id}/export` | Download quiz config as JSON | Returns the full row including private fields |
| `GET /attempts/{id}/artifacts*` | Download attempt artifacts | No `attempt.mode` gate (audit attempts leak) and no `created_by` ownership check |

The agent also sees `tests/test_smoke.py` — naturalistic integration tests
showing the legitimate student + instructor flows ("alice duplicates a quiz,"
"alice shares her copy," "instructor creates a quiz"). It encodes the
route-to-role mapping without saying anything about redaction or fix shape.

---

## 4. The bug, as code, and why an engineer would ship it

The read endpoints just `return quiz` — the full in-memory row. That is the
single most common "convenience read API" pattern in real codebases: the
endpoint returns the whole record "for development convenience," and someone
forgets that the record now carries production-private fields.

The sharp edge is the **duplicate-then-X laundering chain**. `POST
/duplicate` does a `copy.deepcopy` of the source row — so the clone inherits
`answer_bundle` from a quiz the student never authored. The student now owns
that clone, so every legitimate write endpoint on it (`PATCH`, `share`,
`export`) re-serializes the inherited private fields. Each is a separate
leak: a fix that redacts `GET /quizzes/{id}` but not the PATCH response is
still broken. Every multi-tenant SaaS with a "fork" or "clone" feature has to
decide whether the fork inherits private parent fields — many fail this on
first design.

---

## 5. The rubric — what counts as a good test suite

13 weighted criteria in three structural groups:

**Read-side leak coverage** (5 criteria, all major)
1. Non-instructor `GET /quizzes/{id}` redacts private `answer_bundle` fields
2. Non-instructor `GET /quiz-bank` (list) redacts every row
3. Non-instructor `GET /quizzes/{id}/resources/{name}` 4xx for files in `hidden_resource_files`
4. Non-instructor `GET /attempts/{id}/artifacts*` 4xx when `attempt.mode` is an `*_audit` mode
5. Non-instructor `GET /attempts/{id}/artifacts*` 4xx when `created_by != caller.user_id`

**Write-side laundering coverage** (3 criteria, all major)
6. Duplicate-then-PATCH — duplicate a quiz, PATCH the clone, assert no leak in the PATCH response
7. Duplicate-then-share — same chain via `/share`
8. Duplicate-then-export — same chain via `/export`

**Anti-overblock regression guards** (5 criteria, varying severity)
9. **Instructor `GET /quiz-bank` STILL returns full data** (major)
10. Students can still call `/duplicate`, `/share`, `/export` on own resources (major)
11. Non-instructor can still download the public handout file (minor)
12. Path traversal containment — `..` segments / `.key/` prefix (minor)
13. Sentinel marker bytes + zip-content inspection rigor (nitpick)

The anti-overblock guards are why the suite must articulate **both** halves
of the dual contract: "redact for students" AND "preserve instructor access /
preserve legitimate student writes." A suite with only leak-coverage tests
admits both correct and over-blocking fixes — it does not constrain the fix
shape. RUB-013 goes beyond status codes: the agent seeds random sentinel
bytes into the answer key and asserts those bytes never appear in a student
response, including inside a zip archive — catching fixes that return a 200
with redacted JSON but leave the bytes reachable through another path.

---

## 6. How calibration runs work

When a task declares `pipeline: aspen` with `ground_truth_issues[]`, the
platform auto-generates one `nl_assertion` criterion per issue. The LLM judge
reads the agent's trajectory + final diff and scores each criterion 0/1,
weighted by severity. The score formula:

```
reward = sum(score_i * weight_i) / sum(weight_i)
```

Max weight here = 35 (10 majors × 3 + 2 minors × 2 + 1 nitpick × 1).

Calibration uses the live Realm triad — `claude-opus-4-7`,
`gemini-3.1-pro-preview`, `openrouter/qwen/qwen3.5-397b-a17b` — with a
per-model saturation-aware escalation ladder (escalate only models that hit
1.0 at round 1; always escalate the high-variance model for n=10).

---

## 7. How to read the calibration numbers

Once `README.md`'s calibration section is filled, the load-bearing data is
the per-rubric catch-rate table. Three things to check:

1. **Spread** — max catch rate minus min. A healthy task spans roughly
   "every model catches" down to "one model in many attempts."
2. **Shape** — are there distinct ladder rungs (frontier-saturated, mid-tier,
   hard, top-of-frontier), or is it a flat pass/fail?
3. **Top rung** — at least one item caught by `≤10%` of runs is the
   discrimination signal. The expected candidates here are RUB-006
   (duplicate-then-PATCH) and RUB-009 (instructor-still-sees-data) — chained
   reasoning and the dual-contract blind spot are the hardest to induce.

A low score is not automatically a task defect — Aspen is designed to make
models fail rubric items. But if the strongest model reproducibly floors,
re-run it 2–3× to separate variance from a real over-hard rubric before
changing anything.

---

## 8. What this rubric does not measure

- **Fix correctness.** The agent tests the bug, it does not fix it.
- **Cross-language test authoring.** The rubric is Python-pytest specific.
- **Test code quality** (style, naming, DRY-ness). The rubric is a
  threat-model coverage check, not a code-review check.
