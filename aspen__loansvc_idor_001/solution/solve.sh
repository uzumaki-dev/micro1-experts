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
+def test_oracle_rubric():
+    """MAJOR — RUB-001: <RUBRIC_DESCRIPTION>"""
+    pass
+
+def test_oracle_rubric():
+    """MAJOR — RUB-002: <RUBRIC_DESCRIPTION>"""
+    pass
+
+def test_oracle_rubric():
+    """MINOR — RUB-003: <RUBRIC_DESCRIPTION>"""
+    pass
+
+def test_oracle_rubric():
+    """MINOR — RUB-004: <RUBRIC_DESCRIPTION>"""
+    pass
+
+def test_oracle_rubric():
+    """NITPICK — RUB-005: <RUBRIC_DESCRIPTION>"""
+    pass
+
+def test_oracle_rubric():
+    """NITPICK — RUB-006: <RUBRIC_DESCRIPTION>"""
+    pass
DIFF_EOF

echo "Wrote oracle answer.diff stub to /repo/answer.diff (6 placeholder tests)."