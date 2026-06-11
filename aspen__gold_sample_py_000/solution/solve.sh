#!/usr/bin/env bash
# Oracle solution for Aspen: writes a placeholder unified-diff stub derived
# from the ground_truth_issues rubric. Used for sanity-checking the verifier
# pipeline; the judge inspects /repo/answer.diff as text and never applies it.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_oracle_rubric.py b/tests/exfiltration/test_oracle_rubric.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_oracle_rubric.py
@@ -0,0 +1,13 @@
+"""Oracle stub — one placeholder test per ground_truth_issues entry.
+
+These are not real tests; they exist only so the verifier pipeline can be
+exercised end-to-end. The judge will grade them as not-satisfying and emit
+reward=0.
+"""
+
+def test_oracle_stub():
+    """Placeholder test demonstrating the expected submission format."""
+    # A real test would exercise the TaskHub API endpoints and assert
+    # that unauthorized access is blocked while legitimate flows work.
+    # Example: assert that a participant cannot read another participant's
+    # task artifacts, but can read their own.
+    pass
+
+DIFF_EOF
+
+echo "Wrote oracle answer.diff stub to /repo/answer.diff."