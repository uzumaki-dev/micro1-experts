#!/usr/bin/env bash
# Oracle solution for TestGen: writes a placeholder unified-diff stub derived
# from the agent_judge.toml rubric. Used for sanity-checking the verifier
# pipeline; the judge inspects /repo/answer.diff as text and never applies it.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/<TEST_DIR>/test_oracle_rubric.py b/<TEST_DIR>/test_oracle_rubric.py
new file mode 100644
--- /dev/null
+++ b/<TEST_DIR>/test_oracle_rubric.py
@@ -0,0 +1,6 @@
+"""Oracle stub — one placeholder test per agent_judge.toml criterion.
+
+These are not real tests; they exist only so the verifier pipeline can be
+exercised end-to-end. The judge will grade them as not-satisfying and emit
+reward=0.
+"""
+def test_oracle_stub_1():
+    """rub_001 (weight 3.0) — access_control"""
+    pass
+
+def test_oracle_stub_2():
+    """rub_002 (weight 3.0) — <category>"""
+    pass
+
+def test_oracle_stub_3():
+    """rub_003 (weight 2.0) — <category>"""
+    pass
+
+def test_oracle_stub_4():
+    """rub_004 (weight 2.0) — regression_guard"""
+    pass
+
+def test_oracle_stub_5():
+    """rub_005 (weight 1.0) — regression_guard"""
+    pass
+
+def test_oracle_stub_6():
+    """rub_006 (weight 1.0) — reward_hacking [NEGATIVE]"""
+    pass
DIFF_EOF

echo "Wrote oracle answer.diff stub to /repo/answer.diff (6 placeholder tests)."