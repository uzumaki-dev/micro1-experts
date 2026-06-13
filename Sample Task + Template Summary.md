# **TestGen Gold Samples \+ Template**

| Directory | What it is |
| :---- | :---- |
| [`aspen__gold_sample_go_000/`](https://drive.google.com/file/d/1gP_KPNiaXlDv6a12m1gEf42eQLB5AONg/view?usp=drive_link) | Public repo sample task (Go): **Wails assetserver path-traversal** |
| [`aspen__gold_sample_py_000/`](https://drive.google.com/file/d/11U5Da3et7UmaV1a_Yyx-ROk9vD1gKtEw/view?usp=drive_link) | Hand-authored sample task (Python): **TaskHub API IDOR/artifact exfiltration** |
| [`aspen__template_000/`](https://drive.google.com/file/d/1EndE9Va9nA1XptcChbQ-D2cqvmRSZ1E_/view?usp=drive_link) | Blank task skeleton; copy and fill in for a new scenario |

## **Task Summary**

Go golden sample:  
This sample targets a public upstream repo ([Wails](https://github.com/wailsapp/wails/tree/master/v2/pkg/assetserver)). The agent receives a bug report about the Wails dev asset server serving files outside its configured root, and must write Go tests that catch it. It has a 12-item rubric and completed calibration results. Read its `README.md` for the scenario summary.

Python golden sample:  
This sample uses a hand-authored substrate (a mock FastAPI implementation of TaskHub) included in `environment/substrate/`. The agent receives a bug report about unauthorized access to private task artifacts in a TaskHub API, and must write Python tests that catch it. It has a 13-item rubric and TBD calibration results. Read its `README.md` for the scenario summary and `NOTES.md` for design rationale.

Template:  
A task skeleton with TODOs in the key files:

* `instruction.md`  
* `agent_judge.toml`  
* `prompt.md`  
* `solve.sh`  
* `Dockerfile`

Fill those in, upload to Realm, and iterate from there. `AGENTS.md` describes the evaluation pipeline if an AI assistant is helping author the task.

## **Task lifecycle**

Copy [`aspen__template_000/`](https://drive.google.com/file/d/1EndE9Va9nA1XptcChbQ-D2cqvmRSZ1E_/view?usp=drive_link), fill in the five key files, and test through Realm. The gold sample is a worked example of every phase.

1. *Pick scenario \+ substrate*

   * A self-contained behavior with a natural dual contract (a leak to catch and a legitimate flow that must not break).

   * Scope to a single package; avoid scenarios already exhaustively tested upstream.

   * A smoke test baked into the image. Model scores floor without it.

2. *Copy the template*

3. *Package the substrate*

4. *Lock the base\_commit*

   * The squashed SHA must be identical on every build, or the verifier can't isolate the agent's diff.

5. *Author the eval logic*

   * Rubric: ≤20 items

   * Weights ∈ {1,2,3}

   * ≥30% negative items

   * ≥1 `regression_guard` dual-contract item

   * ≥1 `test_quality` sentinel-byte item.

6. *Upload \+ calibrate*

   * Opus ≥80% (task is solvable).

   * All four Qwen runs in 25–50% (task discriminates).

   * If Qwen saturates, tighten the negative items or obfuscate the prompt.

   * If Opus floors, simplify `instruction.md` or loosen a criterion.

7. *Iterate on rubric/instruction*

8. *Document \+ submit*

   * Reupload zip with updated README