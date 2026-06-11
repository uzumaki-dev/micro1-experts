<!--
Agent-facing problem statement. For testgen (test authoring) the agent is asked
to write tests that catch a specific hidden vulnerability/regression in the
target. Describe the surface and what behaviour the tests must exercise — but
do NOT reveal the ground-truth issues; those live only as [[criterion]]
entries in tests/review/agent_judge.toml. Lint requires at least one criterion.

An agent-as-judge will compare your submitted diff against a hidden rubric of
ground-truth issues — for each item it asks: *would the test described by this
diff catch this specific issue?*

!! DELETE THIS COMMENT BEFORE SUBMISSION !!
-->

A participant on our eval platform pinged me — they think they can read back files from tasks they didn't create. Said they were "poking around the API" with their normal participant key and stumbled into something that looked like another author's gold patch. They've been trying different things and keep finding stuff they shouldn't.

We don't have any tests covering this. Your job is to write the test suite that catches it.

**Write tests only. Do not modify any file under `taskhub/`.** A separate engineer will use your tests to validate their fix; for them to trust your tests, the suite must (1) catch the leak the participant is exploiting and (2) catch a fix that over-blocks legitimate participant or admin flows.

Put your tests under `tests/exfiltration/`. `tests/test_smoke.py` shows the legitimate participant + admin flows already in use — your suite should pin those down with anti-overblock assertions so they cannot regress.
