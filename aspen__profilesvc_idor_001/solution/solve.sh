#!/usr/bin/env bash
# Oracle: writes a complete IDOR test suite to /repo/answer.diff.
# Covers all 13 positive rubric items (rub_001–013, rub_021); negative items satisfied by clean code.
set -euo pipefail

mkdir -p "$(dirname "/repo/answer.diff")"

cat > "/repo/answer.diff" <<'DIFF_EOF'
diff --git a/tests/exfiltration/test_profile_idor.py b/tests/exfiltration/test_profile_idor.py
new file mode 100644
--- /dev/null
+++ b/tests/exfiltration/test_profile_idor.py
@@ -0,0 +1,190 @@
+"""Oracle IDOR test suite for profilesvc.
+
+Every test seeds sentinel values into private fields of Alice's profile, then
+asserts those sentinels are absent from responses issued to an unauthenticated
+stranger (Mallory). Regression-guard tests confirm owner and admin flows survive.
+"""
+import pytest
+from fastapi.testclient import TestClient
+
+from profilesvc.app import app
+from profilesvc import store
+
+
+@pytest.fixture(autouse=True)
+def _reset():
+    store.reset()
+    yield
+
+
+@pytest.fixture
+def client():
+    return TestClient(app)
+
+
+def _h(user_id: str) -> dict:
+    return {"X-User-Id": user_id}
+
+
+SENTINEL_SUMMARY = "PRIV_SENTINEL_a3f7b291"
+SENTINEL_SALARY = "SALARY_SENTINEL_d4e8c012"
+SENTINEL_DOC = "DOC_SENTINEL_b5f2a883"
+
+
+@pytest.fixture
+def alice_profile(client):
+    """Alice's private profile with sentinels seeded in all private fields."""
+    r = client.post("/profiles", json={
+        "display_name": "Alice Smith",
+        "headline": "Senior Engineer",
+        "private_summary": SENTINEL_SUMMARY,
+        "experience": [
+            {
+                "title": "Senior Engineer",
+                "company": "Acme Corp",
+                "years": 3.0,
+                "salary_band": SENTINEL_SALARY,
+            }
+        ],
+        "documents": {"portfolio.pdf": SENTINEL_DOC},
+        "visibility": "private",
+    }, headers=_h("alice"))
+    assert r.status_code == 201
+    return r.json()
+
+
+# --- rub_001: GET /profiles/{id} hides private_summary from stranger ---
+
+def test_get_profile_hides_private_summary_from_stranger(client, alice_profile):
+    r = client.get(f"/profiles/{alice_profile['id']}", headers=_h("mallory"))
+    assert SENTINEL_SUMMARY not in r.text
+
+
+# --- rub_002: GET /profiles list hides private_summary from stranger ---
+
+def test_list_profiles_hides_private_summary_from_stranger(client, alice_profile):
+    r = client.get("/profiles", headers=_h("mallory"))
+    assert SENTINEL_SUMMARY not in r.text
+
+
+# --- rub_003: GET /profiles/search hides private_summary from stranger ---
+
+def test_search_profiles_hides_private_summary_from_stranger(client, alice_profile):
+    r = client.get("/profiles/search", params={"q": "Alice"}, headers=_h("mallory"))
+    assert SENTINEL_SUMMARY not in r.text
+
+
+# --- rub_004: GET /profiles/{id}/experience hides salary_band from stranger ---
+
+def test_get_experience_hides_salary_band_from_stranger(client, alice_profile):
+    r = client.get(f"/profiles/{alice_profile['id']}/experience",
+                   headers=_h("mallory"))
+    assert SENTINEL_SALARY not in r.text
+
+
+# --- rub_005: GET /profiles/{id}/export?format=json hides private_summary ---
+
+def test_export_json_hides_private_summary_from_stranger(client, alice_profile):
+    r = client.get(f"/profiles/{alice_profile['id']}/export",
+                   params={"format": "json"}, headers=_h("mallory"))
+    assert SENTINEL_SUMMARY not in r.text
+
+
+# --- rub_006: GET /profiles/{id}/export?format=csv hides private data ---
+
+def test_export_csv_hides_private_data_from_stranger(client, alice_profile):
+    r = client.get(f"/profiles/{alice_profile['id']}/export",
+                   params={"format": "csv"}, headers=_h("mallory"))
+    assert SENTINEL_SUMMARY not in r.text
+    assert SENTINEL_SALARY not in r.text
+
+
+# --- rub_007: GET /profiles/{id}/documents hides document content from stranger ---
+
+def test_get_document_hides_content_from_stranger(client, alice_profile):
+    r = client.get(f"/profiles/{alice_profile['id']}/documents",
+                   params={"name": "portfolio.pdf"}, headers=_h("mallory"))
+    assert SENTINEL_DOC not in r.text
+
+
+# --- rub_008: path traversal in documents is blocked ---
+
+def test_path_traversal_in_documents_does_not_expose_sentinel(client, alice_profile):
+    r = client.get(f"/profiles/{alice_profile['id']}/documents",
+                   params={"name": "../portfolio.pdf"}, headers=_h("mallory"))
+    assert r.status_code in (400, 403, 404) or SENTINEL_DOC not in r.text
+
+
+# --- rub_009: fork-then-PATCH laundering does not expose private_summary ---
+
+def test_fork_then_patch_does_not_launder_private_summary(client, alice_profile):
+    fork_r = client.post(f"/profiles/{alice_profile['id']}/fork",
+                         headers=_h("mallory"))
+    assert fork_r.status_code == 201
+    fork_id = fork_r.json()["id"]
+    assert SENTINEL_SUMMARY not in fork_r.text
+
+    patch_r = client.patch(f"/profiles/{fork_id}",
+                           json={"display_name": "Mallory Profile"},
+                           headers=_h("mallory"))
+    assert SENTINEL_SUMMARY not in patch_r.text
+
+
+# --- rub_010: stranger can still GET a public-visibility profile ---
+
+def test_stranger_can_access_public_profile(client):
+    r = client.post("/profiles", json={
+        "display_name": "Public Speaker",
+        "visibility": "public",
+    }, headers=_h("alice"))
+    assert r.status_code == 201
+    profile_id = r.json()["id"]
+
+    r2 = client.get(f"/profiles/{profile_id}", headers=_h("mallory"))
+    assert r2.status_code == 200
+    assert "Public Speaker" in r2.json()["display_name"]
+
+
+# --- rub_011: fork-then-export laundering does not expose private data ---
+
+def test_fork_then_export_does_not_launder_private_data(client, alice_profile):
+    fork_r = client.post(f"/profiles/{alice_profile['id']}/fork",
+                         headers=_h("mallory"))
+    assert fork_r.status_code == 201
+    fork_id = fork_r.json()["id"]
+    assert SENTINEL_SUMMARY not in fork_r.text
+
+    exp_r = client.get(f"/profiles/{fork_id}/export",
+                       params={"format": "json"}, headers=_h("mallory"))
+    assert SENTINEL_SUMMARY not in exp_r.text
+    assert SENTINEL_SALARY not in exp_r.text
+
+
+# --- rub_012: owner GET still returns private_summary (regression guard) ---
+
+def test_owner_can_still_read_own_private_summary(client, alice_profile):
+    r = client.get(f"/profiles/{alice_profile['id']}", headers=_h("alice"))
+    assert r.status_code == 200
+    assert SENTINEL_SUMMARY in r.json()["private_summary"]
+
+
+# --- rub_013: admin GET still returns private_summary (regression guard) ---
+
+def test_admin_can_still_read_private_summary(client, alice_profile):
+    r = client.get(f"/profiles/{alice_profile['id']}", headers=_h("admin"))
+    assert r.status_code == 200
+    assert SENTINEL_SUMMARY in r.json()["private_summary"]
+
+
+# --- rub_014: non-owner can create and find own profile in list (regression guard) ---
+
+def test_non_owner_can_create_and_list_own_profile(client):
+    create_r = client.post("/profiles", json={"display_name": "Bob Jones"},
+                           headers=_h("bob"))
+    assert create_r.status_code == 201
+    profile_id = create_r.json()["id"]
+
+    list_r = client.get("/profiles", headers=_h("bob"))
+    assert list_r.status_code == 200
+    ids = [p["id"] for p in list_r.json()]
+    assert profile_id in ids
DIFF_EOF

echo "Wrote oracle solution to /repo/answer.diff."
