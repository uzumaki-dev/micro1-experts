#  What is rv?

rv is a command-line tool that will allow you to build harbor tasks **faster** and with **less reworks**, while **improving quality**. It provides project specific checks and templates.

# Installation

1. Install docker: [https://docs.docker.com/desktop/setup/install/windows-install/](https://docs.docker.com/desktop/setup/install/windows-install/) (alternatives e.g. colima, rancher should work also)  
2. Install uv: [https://docs.astral.sh/uv/getting-started/installation/](https://docs.astral.sh/uv/getting-started/installation/)  
3. Install opencode: [https://opencode.ai/download](https://opencode.ai/download)  
4. Install gcloud: [https://docs.cloud.google.com/sdk/docs/install-sdk](https://docs.cloud.google.com/sdk/docs/install-sdk)

Finally, install rv:

```shell
gcloud auth login # Log in with your micro1 account
gcloud auth application-default login 

# 1. Set up keyring auth for the private registry
uv tool install keyring --with keyrings.google-artifactregistry-auth

# 2. Install rv itself
uv tool install --keyring-provider subprocess \
  --index https://oauth2accesstoken@us-central1-python.pkg.dev/m1-rl-envs/rv-coding/simple/ \
  realm-verifier

# 3. Install harbor (the container orchestrator rv depends on)
uv tool install harbor
```

**If you face a gcloud auth issue please DM a HDM/HDL/SPL**

Verify the install:

```shell
rv health        # checks Docker, harbor, and opencode are configured
```

Then provision your credentials (one time):

```shell
rv auth          # provisions your capped OpenRouter API key + saves your email
```

# Quick Start

```shell
rv health                       # confirm docker / harbor / opencode are ready
rv init devops__cron-broken     # scaffold a new task from a realm template
cd devops__cron-broken
rv check                        # run lint rules + LLM quality rubrics
rv oracle                       # run the reference solution + verifier
rv run         # evaluate a real agent against the task
rv analyze                      # inspect the agent's trial trajectories
rv submit                       # zip the task into ./submission.zip
```

# Commands

| Command | What it does |
| :---- | :---- |
| rv | Launches an opencode session using a pre-selected model |
| rv init \[NAME\] | Scaffold a new task directory from a realm template. (Template selection is interactive) |
| rv check | Run the realm's deterministic lint rules **plus** LLM-judged quality rubrics. |
| rv oracle | Run the task's solve.sh reference solution through the verifier. This is how you prove the task is actually solvable. Use during authoring. |
| rv run NAME | Evaluate a real LLM agent (e.g. opencode, claude-code) against the task. |
| rv analyze | Analyze trial trajectories. With no argument (in a task dir) it opens a picker over that task's jobs/. Pass a path to skip the picker. |
| rv view | Launch harbor view to browse the task's trajectories interactively. |
| rv shell | Drop into an interactive shell inside the task's container environment. |
| rv submit | Run the lint gate, then zip the task into ./submission.zip for upload. Blocks if lint fails. |
| rv health | Verify Docker, harbor, and opencode are configured. |
| rv auth | Provision your OpenRouter key and save your email, then run health checks. |
| rv update | Reinstall the latest rv from the registry. |

###  Important nuance: check vs submit

- rv check runs **both** the deterministic lint rules **and** the LLM quality rubrics (verifiable, well-specified, solvable, outcome-verified).  
- rv submit only runs the lint rules as a gate. It does **not** run the LLM rubrics, the oracle, the eval, or analyze.

**So before you submit, you should run rv check, rv oracle, rv run, and rv analyze yourself.** submit is just the final packaging step; it does not re-validate quality for you.  
