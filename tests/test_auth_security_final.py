#!/usr/bin/env python3
"""
Automated Security Tests for APH SmartSearch AI — Final Authentication & Authorization Hardening.

Verification Scope:
1. Staff Impersonation Defense: Knowing a valid staff ID alone cannot issue tokens.
2. Credential Verification: Passwords are strictly verified using PBKDF2-HMAC-SHA256.
3. Role Escalation Defense: Client-supplied roles are completely ignored; roles are derived strictly from internal registry.
4. Browser PDF Link Click Security: Authenticated staff access protected PDFs via HttpOnly SameSite cookies without tokens in URLs.
5. Direct File Vault Authorization: Direct downloads of protected PDFs enforce equivalent RBAC (HTTP 403 for unauthorized requests).
6. Direct Cache & Database Storage Protection: Direct access to /data/pdf_cache/, *.db, and .session_secret returns HTTP 403.
7. Public Access Integrity: Approved public forms remain accessible without credentials.
"""

import unittest
import os
import sys
import json
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security_auth import (
    create_signed_session_token,
    authenticate_and_issue_staff_token,
    verify_password,
    hash_password,
    ACCESS_PUBLIC,
    ACCESS_STAFF,
    ACCESS_CLINICAL,
    ACCESS_MANAGEMENT
)

SERVER_BASE = "http://localhost:3000"


def send_http_request(url: str, method: str = "GET", headers: dict = None, data: bytes = None):
    req = urllib.request.Request(url, headers=headers or {}, method=method, data=data)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


class TestAuthSecurityFinalHardening(unittest.TestCase):

    # =========================================================================
    # 1. STAFF IMPERSONATION & CREDENTIAL AUDIT
    # =========================================================================

    def test_01_impersonation_without_password_rejected(self):
        """Knowing a valid doctor staff ID alone cannot issue an authentication token."""
        payload = json.dumps({"staff_id": "dr_clinical_101"}).encode("utf-8")
        status, _, body = send_http_request(
            f"{SERVER_BASE}/api/auth/token",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=payload
        )
        self.assertEqual(status, 401)
        resp = json.loads(body.decode("utf-8"))
        self.assertIn("Password is required", resp.get("error", ""))
        self.assertIn("Knowing a staff ID alone cannot issue", resp.get("error", ""))

    def test_02_impersonation_with_wrong_password_rejected(self):
        """Supplying an incorrect password fails authentication with 401."""
        payload = json.dumps({
            "staff_id": "dr_clinical_101",
            "password": "WrongPassword!2026"
        }).encode("utf-8")
        status, _, body = send_http_request(
            f"{SERVER_BASE}/api/auth/token",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=payload
        )
        self.assertEqual(status, 401)
        resp = json.loads(body.decode("utf-8"))
        self.assertIn("Invalid staff password", resp.get("error", ""))

    def test_03_unknown_staff_id_rejected(self):
        """Non-existent or forged staff ID is rejected with 401."""
        payload = json.dumps({
            "staff_id": "attacker_user_999",
            "password": "AnyPassword!"
        }).encode("utf-8")
        status, _, body = send_http_request(
            f"{SERVER_BASE}/api/auth/token",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=payload
        )
        self.assertEqual(status, 401)
        resp = json.loads(body.decode("utf-8"))
        self.assertIn("not recognized", resp.get("error", ""))

    def test_04_role_escalation_attempt_ignored(self):
        """Staff user cannot escalate privileges to MANAGEMENT by passing 'role' in payload."""
        payload = json.dumps({
            "staff_id": "staff_user",
            "password": "StaffUser#2026!",
            "role": "MANAGEMENT"  # Attempted escalation
        }).encode("utf-8")
        status, _, body = send_http_request(
            f"{SERVER_BASE}/api/auth/token",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=payload
        )
        self.assertEqual(status, 200)
        resp = json.loads(body.decode("utf-8"))
        # Must be assigned STAFF, never MANAGEMENT
        self.assertEqual(resp.get("role"), ACCESS_STAFF)
        self.assertNotEqual(resp.get("role"), ACCESS_MANAGEMENT)

    def test_05_verified_clinical_authentication_succeeds_with_cookie(self):
        """Valid doctor credentials issue a signed token and Set-Cookie header."""
        payload = json.dumps({
            "staff_id": "dr_clinical_101",
            "password": "Clinical#2026!"
        }).encode("utf-8")
        status, headers, body = send_http_request(
            f"{SERVER_BASE}/api/auth/token",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=payload
        )
        self.assertEqual(status, 200)
        resp = json.loads(body.decode("utf-8"))
        self.assertEqual(resp.get("role"), ACCESS_CLINICAL)
        self.assertTrue(resp.get("token", "").startswith("aph_s_"))

        # Verify Set-Cookie header for clean browser PDF navigation
        cookie = headers.get("Set-Cookie", "")
        self.assertIn("aph_session=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Strict", cookie)

    # =========================================================================
    # 2. BROWSER PDF LINK & DIRECT FILE ACCESS SECURITY
    # =========================================================================

    def test_06_browser_cookie_authorizes_pdf_link_without_url_token(self):
        """Authenticated staff can open protected PDF link using session cookie without tokens in URL."""
        # 1. Log in to get token
        is_auth, token, role, _ = authenticate_and_issue_staff_token("dr_clinical_101", "Clinical#2026!")
        self.assertTrue(is_auth)

        # 2. Access protected clinical CPR guideline using Cookie header (standard browser navigation)
        cpr_url = f"{SERVER_BASE}/files/nabh/COP%205%20GUIDELINE%20FOR%20CPR.pdf"
        status, _, body = send_http_request(
            cpr_url,
            headers={"Cookie": f"aph_session={token}"}
        )
        self.assertEqual(status, 200)
        self.assertGreater(len(body), 10_000)
        self.assertTrue(body.startswith(b"%PDF"))

    def test_07_unauthorized_direct_pdf_download_fails_closed(self):
        """Direct GET /files/... for clinical PDF without authorization returns HTTP 403."""
        cpr_url = f"{SERVER_BASE}/files/nabh/COP%205%20GUIDELINE%20FOR%20CPR.pdf"
        status, _, body = send_http_request(cpr_url)
        self.assertEqual(status, 403)
        self.assertIn(b"Access Denied", body)
        self.assertIn(b"CLINICAL", body)

    def test_08_insufficient_role_pdf_download_fails_closed(self):
        """General staff user attempting to download CLINICAL PDF returns HTTP 403."""
        is_auth, staff_token, _, _ = authenticate_and_issue_staff_token("staff_user", "StaffUser#2026!")
        self.assertTrue(is_auth)

        cpr_url = f"{SERVER_BASE}/files/nabh/COP%205%20GUIDELINE%20FOR%20CPR.pdf"
        status, _, body = send_http_request(
            cpr_url,
            headers={"Authorization": f"Bearer {staff_token}"}
        )
        self.assertEqual(status, 403)
        self.assertIn(b"CLINICAL", body)

    def test_09_public_pdf_accessible_without_auth(self):
        """Approved public consent form can be downloaded by anyone without credentials."""
        public_url = f"{SERVER_BASE}/files/INFORMED%20CONSENT%20FORM%20FOR%20SURGERY%20OR%20PROCEDURES-Tamil.pdf"
        status, _, body = send_http_request(public_url)
        self.assertEqual(status, 200)
        self.assertGreater(len(body), 10_000)
        self.assertTrue(body.startswith(b"%PDF"))

    # =========================================================================
    # 3. DIRECT BACKEND STORAGE ACCESS PROTECTION
    # =========================================================================

    def test_10_direct_data_pdf_cache_bypass_blocked(self):
        """Direct access to internal /data/pdf_cache/ directory is blocked with HTTP 403."""
        cache_url = f"{SERVER_BASE}/data/pdf_cache/COP_5_GUIDELINE_FOR_CPR.pdf"
        status, _, body = send_http_request(cache_url)
        self.assertEqual(status, 403)
        self.assertIn(b"Access to sensitive file or configuration is strictly prohibited", body)

    def test_11_direct_database_file_download_blocked(self):
        """Direct download of SQLite index database is blocked with HTTP 403."""
        db_url = f"{SERVER_BASE}/data/aph_knowledge_index.db"
        status, _, body = send_http_request(db_url)
        self.assertEqual(status, 403)

    def test_12_secret_session_file_download_blocked(self):
        """Direct download of cryptographic session secret file is blocked with HTTP 403."""
        secret_url = f"{SERVER_BASE}/data/.session_secret"
        status, _, body = send_http_request(secret_url)
        self.assertEqual(status, 403)


if __name__ == "__main__":
    unittest.main()
