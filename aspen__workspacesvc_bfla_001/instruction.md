<!--
Agent-facing problem statement. For testgen (test authoring) the agent is asked
to write tests that catch a specific hidden vulnerability/regression in the
target. Describe the surface and what behaviour the tests must exercise — but
do NOT reveal the ground-truth issues; those live only as [[criterion]]
entries in tests/review/agent_judge.toml. Lint requires at least one criterion.

An agent-as-judge will compare your submitted diff against a hidden rubric of
ground-truth issues — for each item it asks: *would the test described by this
diff catch this specific issue?*

Write a realistic test scenario. Refer to the golden sample for a sample prompt.

!! DELETE THIS COMMENT BEFORE SUBMISSION !!
-->
