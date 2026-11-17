#!/usr/bin/env python3
"""
Automated Security Tests for APH SmartSearch AI — Authentication Hardening Verification.

Verification Scope:
1. Staff Impersonation Defense: Knowing a valid staff ID alone cannot issue tokens.
2. Credential Verification: Passwords are strictly verified using PBKDF2-HMAC-SHA256.
3. Role Escalation Defense: Client-supplied roles are completely ignored; roles are derived strictly from internal registry.
4. Browser PDF Link Click Security: Authenticated staff access protected PDFs via HttpOnly SameSite cookies without tokens in URLs.
5. Direct File Vault Authorization: Direct downloads of protected PDFs enforce equivalent RBAC (HTTP 403 for unauthorized requests).
6. Direct Cache & Database Storage Protection: Direct access to /data/pdf_cache/, *.db, and secret files returns HTTP 403.
7. Service Key & Session Secret Isolation: Session secret cannot be used as password or service key.
8. Dedicated Service Identity: Service accounts are narrowly scoped and cannot masquerade as human doctors or admins.
9. Password Directory Audit: Unique salts per account, no shared hashes, no plaintext passwords.
10. Account Lockout: 5 consecutive failures locks the staff account with 423 Locked / 401.
11. Login Rate Limiting: IP-based rate limiting returns 429 Too Many Requests with Retry-After.
12. Logout & Token Revocation: /api/auth/logout revokes tokens immediately and clears the session cookie.
13. Session Expiration: Expired tokens fail closed to ACCESS_PUBLIC.
14. Cross-Host Intranet Verification: Host header 192.168.101.75:3000 enforces authorization independently.
15. Cross-Host Browser Navigation & CORS: Access-Control-Allow-Credentials: true emitted for trusted origins.
16. HTTPS Secure Cookie: Secure flag appended when HTTPS transport is active or enforced.
"""

import unittest
import os
import sys
import json
import time
import urllib.request
import urllib.error

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from security_auth import (
    create_signed_session_token,
    authenticate_and_issue_staff_token,
    authenticate_service_identity,
    verify_signed_session_token,
    verify_staff_directory_security,
    revoke_token,
    is_token_revoked,
    is_account_locked,
    unlock_staff_account,
    reset_rate_limit_tracking,
    build_session_cookie,
    build_logout_cookie,
    SESSION_SECRET,
    INTERNAL_SERVICE_SECRET,
    STAFF_DIRECTORY,
    SERVICE_ACCOUNTS,
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

    def setUp(self):
        # Reset any rate limits or locks between tests
        reset_rate_limit_tracking()
        unlock_staff_account("dr_clinical_101")
        unlock_staff_account("staff_user")
        unlock_staff_account("test_staff")
        try:
            send_http_request(f"{SERVER_BASE}/api/auth/reset-limits", method="POST")
        except Exception:
            pass

    def tearDown(self):
        reset_rate_limit_tracking()
        unlock_staff_account("dr_clinical_101")
        unlock_staff_account("staff_user")
        unlock_staff_account("test_staff")
        try:
            send_http_request(f"{SERVER_BASE}/api/auth/reset-limits", method="POST")
        except Exception:
            pass

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
        self.assertEqual(resp.get("role"), ACCESS_STAFF)
        self.assertNotEqual(resp.get("role"), ACCESS_MANAGEMENT)

    def test_05_verified_clinical_authentication_succeeds_with_cookie(self):
        """Valid doctor credentials issue a signed token and HttpOnly SameSite cookie."""
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

        cookie = headers.get("Set-Cookie", "")
        self.assertIn("aph_session=", cookie)
        self.assertIn("HttpOnly", cookie)
        self.assertIn("SameSite=Lax", cookie)

    # =========================================================================
    # 2. BROWSER PDF LINK & DIRECT FILE ACCESS SECURITY
    # =========================================================================

    def test_06_browser_cookie_authorizes_pdf_link_without_url_token(self):
        """Authenticated staff can open protected PDF link using session cookie without tokens in URL."""
        is_auth, token, role, _ = authenticate_and_issue_staff_token("dr_clinical_101", "Clinical#2026!")
        self.assertTrue(is_auth)

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

    def test_12_secret_files_download_blocked(self):
        """Direct download of session and service secrets is blocked with HTTP 403."""
        for secret_path in ["/data/.session_secret", "/data/.service_secret"]:
            status, _, _ = send_http_request(f"{SERVER_BASE}{secret_path}")
            self.assertEqual(status, 403)

    # =========================================================================
    # 4. SERVICE KEY & SESSION SECRET ISOLATION
    # =========================================================================

    def test_13_session_secret_cannot_be_used_as_password_or_service_key(self):
        """Session-signing secret is strictly isolated and cannot be used as login credential."""
        # A. Attempting to use SESSION_SECRET as password for a doctor account is blocked
        is_auth, err, _, _ = authenticate_and_issue_staff_token("dr_clinical_101", SESSION_SECRET)
        self.assertFalse(is_auth)
        self.assertIn("Session secret cannot be used", err)

        # B. Attempting to use SESSION_SECRET via HTTP login endpoint is rejected
        payload = json.dumps({
            "staff_id": "dr_clinical_101",
            "password": SESSION_SECRET
        }).encode("utf-8")
        status, _, body = send_http_request(
            f"{SERVER_BASE}/api/auth/token",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=payload
        )
        self.assertEqual(status, 401)
        resp = json.loads(body.decode("utf-8"))
        self.assertIn("Session secret cannot be used", resp.get("error", ""))

        # C. Attempting to use SESSION_SECRET as service_key is rejected
        is_auth, err, _, _ = authenticate_service_identity("svc_knowledge_indexer", SESSION_SECRET)
        self.assertFalse(is_auth)
        self.assertIn("Session secret cannot be used", err)

    def test_14_service_accounts_cannot_masquerade_as_clinical_staff(self):
        """Service keys cannot be used to authenticate as human staff members."""
        payload = json.dumps({
            "staff_id": "dr_clinical_101",
            "service_key": INTERNAL_SERVICE_SECRET
        }).encode("utf-8")
        status, _, body = send_http_request(
            f"{SERVER_BASE}/api/auth/token",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=payload
        )
        self.assertEqual(status, 401)
        resp = json.loads(body.decode("utf-8"))
        self.assertIn("Service keys cannot be used to authenticate human staff", resp.get("error", ""))

    def test_15_dedicated_service_identity_authenticated_with_narrow_role(self):
        """Dedicated machine-to-machine service account issues narrowly-scoped token."""
        payload = json.dumps({
            "service_id": "svc_knowledge_indexer",
            "service_key": INTERNAL_SERVICE_SECRET
        }).encode("utf-8")
        status, _, body = send_http_request(
            f"{SERVER_BASE}/api/auth/token",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=payload
        )
        self.assertEqual(status, 200)
        resp = json.loads(body.decode("utf-8"))
        self.assertEqual(resp.get("role"), ACCESS_STAFF)
        self.assertEqual(resp.get("service_id"), "svc_knowledge_indexer")
        self.assertTrue(resp.get("token", "").startswith("aph_s_"))

    # =========================================================================
    # 5. PASSWORD SECURITY AUDIT
    # =========================================================================

    def test_16_staff_directory_has_unique_salts_and_no_plaintext(self):
        """Every staff account has a unique 16-byte cryptographic salt and distinct hash."""
        audit = verify_staff_directory_security()
        self.assertTrue(audit["secure"])
        self.assertEqual(len(audit["issues"]), 0)
        self.assertEqual(audit["unique_salts"], audit["account_count"])
        self.assertEqual(audit["unique_hashes"], audit["account_count"])

    # =========================================================================
    # 6. RATE LIMITING & ACCOUNT LOCKOUT
    # =========================================================================

    def test_17_account_lockout_after_consecutive_failures(self):
        """5 consecutive failed logins locks the staff account."""
        staff_id = "test_staff"
        unlock_staff_account(staff_id)

        # Trigger 5 failed logins
        for i in range(5):
            payload = json.dumps({"staff_id": staff_id, "password": f"BadPassword{i}"}).encode("utf-8")
            status, _, _ = send_http_request(
                f"{SERVER_BASE}/api/auth/token",
                method="POST",
                headers={"Content-Type": "application/json"},
                data=payload
            )
            self.assertEqual(status, 401)

        # 6th attempt (even with valid password) must be rejected due to account lockout
        payload_valid = json.dumps({"staff_id": staff_id, "password": "TestStaffAccount#2026!"}).encode("utf-8")
        status, _, body = send_http_request(
            f"{SERVER_BASE}/api/auth/token",
            method="POST",
            headers={"Content-Type": "application/json"},
            data=payload_valid
        )
        self.assertIn(status, [423, 401])
        resp = json.loads(body.decode("utf-8"))
        self.assertIn("locked", resp.get("error", "").lower())

        # Cleanup
        unlock_staff_account(staff_id)

    def test_18_ip_rate_limiting_enforced(self):
        """Excessive failed attempts from the same IP trigger HTTP 429 Too Many Requests."""
        client_ip = "192.168.101.99"
        for i in range(5):
            payload = json.dumps({"staff_id": f"invalid_user_{i}", "password": "bad"}).encode("utf-8")
            send_http_request(
                f"{SERVER_BASE}/api/auth/token",
                method="POST",
                headers={"Content-Type": "application/json", "X-Forwarded-For": client_ip},
                data=payload
            )

        # 6th attempt from same IP should receive HTTP 429
        payload = json.dumps({"staff_id": "dr_clinical_101", "password": "Clinical#2026!"}).encode("utf-8")
        status, headers, body = send_http_request(
            f"{SERVER_BASE}/api/auth/token",
            method="POST",
            headers={"Content-Type": "application/json", "X-Forwarded-For": client_ip},
            data=payload
        )
        self.assertEqual(status, 429)
        self.assertIn("Retry-After", headers)
        resp = json.loads(body.decode("utf-8"))
        self.assertIn("Too many failed login attempts", resp.get("error", ""))

    # =========================================================================
    # 7. LOGOUT, SESSION EXPIRY & ROLE REVOCATION
    # =========================================================================

    def test_19_logout_endpoint_revokes_token_and_clears_cookie(self):
        """POST /api/auth/logout revokes active token and sets expired session cookie."""
        is_auth, token, _, _ = authenticate_and_issue_staff_token("dr_clinical_101", "Clinical#2026!")
        self.assertTrue(is_auth)

        # Request logout
        status, headers, body = send_http_request(
            f"{SERVER_BASE}/api/auth/logout",
            method="POST",
            headers={"Authorization": f"Bearer {token}", "Cookie": f"aph_session={token}"}
        )
        self.assertEqual(status, 200)
        resp = json.loads(body.decode("utf-8"))
        self.assertEqual(resp.get("status"), "success")

        # Verify cookie is cleared
        set_cookie = headers.get("Set-Cookie", "")
        self.assertIn("aph_session=", set_cookie)
        self.assertIn("Max-Age=0", set_cookie)

        # Verify token is marked revoked
        self.assertTrue(is_token_revoked(token))

    def test_20_revoked_token_cannot_access_restricted_files(self):
        """A revoked token fails closed and cannot access restricted documents."""
        is_auth, token, _, _ = authenticate_and_issue_staff_token("dr_clinical_101", "Clinical#2026!")
        self.assertTrue(is_auth)

        # Revoke the token
        revoke_token(token)

        # Attempt to access clinical document with revoked token
        cpr_url = f"{SERVER_BASE}/files/nabh/COP%205%20GUIDELINE%20FOR%20CPR.pdf"
        status, _, _ = send_http_request(
            cpr_url,
            headers={"Cookie": f"aph_session={token}"}
        )
        self.assertEqual(status, 403)

    def test_21_expired_session_token_fails_closed(self):
        """Tokens with past expiration timestamp fail closed to None / ACCESS_PUBLIC."""
        # Create token that expired 10 seconds ago
        expired_token = create_signed_session_token("dr_clinical_101", ACCESS_CLINICAL, duration_seconds=-10)
        payload = verify_signed_session_token(expired_token)
        self.assertIsNone(payload)

        # Attempt to access clinical document with expired token
        cpr_url = f"{SERVER_BASE}/files/nabh/COP%205%20GUIDELINE%20FOR%20CPR.pdf"
        status, _, _ = send_http_request(
            cpr_url,
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        self.assertEqual(status, 403)

    # =========================================================================
    # 8. CROSS-HOST & INTRANET IP ACCESS
    # =========================================================================

    def test_22_direct_pdf_links_on_intranet_host_enforce_authorization(self):
        """Direct PDF links with Host: 192.168.101.75:3000 enforce authorization independently."""
        intranet_headers = {"Host": "192.168.101.75:3000"}
        cpr_url = f"{SERVER_BASE}/files/nabh/COP%205%20GUIDELINE%20FOR%20CPR.pdf"

        # 1. Unauthenticated request to clinical guideline receives 403
        status, _, _ = send_http_request(cpr_url, headers=intranet_headers)
        self.assertEqual(status, 403)

        # 2. Authenticated request with session cookie receives 200
        is_auth, token, _, _ = authenticate_and_issue_staff_token("dr_clinical_101", "Clinical#2026!")
        auth_headers = {"Host": "192.168.101.75:3000", "Cookie": f"aph_session={token}"}
        status, _, body = send_http_request(cpr_url, headers=auth_headers)
        self.assertEqual(status, 200)
        self.assertTrue(body.startswith(b"%PDF"))

    def test_23_cross_host_browser_navigation_cors_credentials(self):
        """Cross-host requests from trusted origins receive Access-Control-Allow-Credentials: true."""
        req_headers = {
            "Origin": "http://192.168.101.75:3000",
            "Access-Control-Request-Method": "GET"
        }
        status, resp_headers, _ = send_http_request(
            f"{SERVER_BASE}/api/ai-search",
            method="OPTIONS",
            headers=req_headers
        )
        self.assertEqual(status, 204)
        self.assertEqual(resp_headers.get("Access-Control-Allow-Origin"), "http://192.168.101.75:3000")
        self.assertEqual(resp_headers.get("Access-Control-Allow-Credentials"), "true")

    def test_24_https_session_cookie_includes_secure_flag(self):
        """build_session_cookie includes Secure flag when HTTPS is active or enforced."""
        token = "aph_s_sampletoken.signature"
        http_cookie = build_session_cookie(token, is_https=False)
        self.assertIn("HttpOnly", http_cookie)
        self.assertIn("SameSite=Lax", http_cookie)
        self.assertNotIn("Secure", http_cookie)

        https_cookie = build_session_cookie(token, is_https=True)
        self.assertIn("HttpOnly", https_cookie)
        self.assertIn("SameSite=Lax", https_cookie)
        self.assertIn("Secure", https_cookie)


if __name__ == "__main__":
    unittest.main()
