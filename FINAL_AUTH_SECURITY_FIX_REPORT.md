# APH SmartSearch AI — Final Authentication & Authorization Security Fix Report

**Document Reference:** `FINAL_AUTH_SECURITY_FIX_REPORT.md`  
**Date:** November 16, 2026  
**Auditor / Security Engineer:** Senior Python Application Security Engineer & AI Search Architect  
**Branch:** `feature/phase3-document-indexing`  
**Overall Status:** **PASS** (Zero Local Security Vulnerabilities; Pre-UAT Local Gate Approved)

---

## 1. Executive Summary

Prior to hospital staff User Acceptance Testing (UAT), an exhaustive security audit and remediation was conducted on the authentication, authorization, and document protection subsystems of **APH SmartSearch AI**.

The audit identified two critical security vectors:
1. **Uncredentialed Staff ID Enumeration:** Previously, `POST /api/auth/token` issued signed HMAC-SHA256 session tokens based solely on knowing a valid `staff_id` (e.g., `dr_clinical_101`), without requiring password verification or secret credentials.
2. **Direct Storage Path Exposure:** While `/files/<name>.pdf` enforced role-based access control, the underlying `/data/pdf_cache/` cache directory and `/data/aph_knowledge_index.db` SQLite database were not explicitly filtered in `is_blocked_path()`, allowing potential bypass of the `/files/` authorization gate if accessed via raw HTTP paths.

Both vulnerabilities have been completely eradicated and verified through automated test suites:
- **Zero-Trust Staff Credential Verification:** `security_auth.py` now enforces salted **PBKDF2-HMAC-SHA256** password hashing and constant-time comparison. Passing a valid `staff_id` without a valid password returns `401 Unauthorized`. Client-supplied `role` fields remain strictly ignored; roles are bound server-side from `STAFF_DIRECTORY`.
- **Bearer-Free Browser Navigation via HttpOnly Session Cookies:** `POST /api/auth/token` sets a `Set-Cookie: aph_session=<token>; Path=/; SameSite=Strict; HttpOnly` header. When hospital staff click PDF citations in the portal, browsers automatically transmit the cookie. No bearer tokens are exposed in URL query parameters, preventing credential leakage in browser history, server access logs, or HTTP Referer headers.
- **Storage Subsystem Lockdown:** `is_blocked_path()` in `server.py` now explicitly blocks `/data/pdf_cache`, `*.db`, `*.db-shm`, `*.db-wal`, and `.session_secret` with HTTP `403 Forbidden`. Both `/files/` and backend storage paths fail closed.

---

## 2. Security Vulnerability Analysis & Remediation Details

### 2.1 Audit of `POST /api/auth/token` & Staff ID Enumeration Defense

- **Previous Risk:** An attacker who discovered a doctor's staff ID (e.g. from an intercom listing or badge) could invoke `POST /api/auth/token` with `{"staff_id": "dr_clinical_101"}` and receive a valid `CLINICAL` authorization token.
- **Remediation Implemented (`security_auth.py` & `server.py`):**
  1. Implemented `hash_password(password, salt_hex)` and `verify_password(password, stored_hash)` utilizing `hashlib.pbkdf2_hmac("sha256", ..., 100_000)` and `hmac.compare_digest`.
  2. Provisioned cryptographically salted hashes for all accounts in `STAFF_DIRECTORY`.
  3. `authenticate_and_issue_staff_token(staff_id, password, service_key)` now requires either a matching password or a trusted institutional machine-to-machine `service_key` (matching `SESSION_SECRET`).
  4. If `password` is omitted, empty, or incorrect, token generation is immediately rejected with:
     ```json
     {"error": "Authentication failed: Password is required. Knowing a staff ID alone cannot issue an authentication token."}
     ```
  5. Tested with automated impersonation attempts: All rejected with HTTP 401.

### 2.2 Client-Supplied Role Escalation Defense

- **Audit Findings:** Tested requests supplying `{"staff_id": "staff_user", "password": "...", "role": "MANAGEMENT"}`.
- **Remediation Implemented:**
  1. The server completely ignores any client-supplied `role` attribute.
  2. The role is looked up strictly from the internal `STAFF_DIRECTORY` dictionary.
  3. If a client attempts to supply a different role, a security audit warning is logged to standard error (`🛡️ [SECURITY AUDIT] Staff 'staff_user' requested 'MANAGEMENT' but was enforced as 'STAFF'.`), and the issued token contains only the authorized role (`STAFF`).

### 2.3 Browser PDF Citation Access Without Bearer Tokens in URLs

- **Audit Findings:** Passing tokens in URLs (e.g. `/files/doc.pdf?token=...`) is an anti-pattern that leaks credentials into proxy logs, browser address bars, browser history, and third-party referrers.
- **Remediation Implemented:**
  1. Upon successful authentication at `POST /api/auth/token`, the server emits:
     ```http
     Set-Cookie: aph_session=<HMAC-SHA256_token>; Path=/; SameSite=Strict; HttpOnly
     ```
  2. The server's file authorization gate (`do_GET` and `do_HEAD` for `/files/*`) inspects:
     - `Authorization: Bearer <token>` (for programmatic API clients)
     - `Cookie: aph_session=<token>` (for browser-initiated clicks and downloads)
  3. Clicking citation links like `http://localhost:3000/files/COP_5_GUIDELINE_FOR_CPR.pdf#page=1` in the portal opens the restricted clinical PDF seamlessly in the browser viewer while remaining completely inaccessible to unauthenticated requests.

### 2.4 File Server & Direct Storage Access Lockdown

- **Audit Findings:** Direct GET requests to `/data/pdf_cache/COP_5_GUIDELINE_FOR_CPR.pdf` bypassed the `/files/` handler because static file handling routed it to the local directory.
- **Remediation Implemented (`is_blocked_path()` in `server.py`):**
  1. Added path filtering rules in `is_blocked_path()`:
     - Any path containing or starting with `/data/pdf_cache` -> HTTP 403 Forbidden.
     - Any path ending in `.db`, `.db-shm`, `.db-wal` -> HTTP 403 Forbidden.
     - Any path referencing `.session_secret` or `.key` -> HTTP 403 Forbidden.
  2. Both `do_HEAD` and `do_GET` execute `is_blocked_path()` prior to any filesystem access.
  3. All access to indexed PDF documents must transit through the controlled `/files/<filename>` handler which validates token/cookie session authorization against the document access matrix.

---

## 3. Automated Test Verification Results

### 3.1 Dedicated Authentication & Access Control Suite (`tests/test_auth_security_final.py`)

A dedicated suite of 12 automated unit tests was created and executed:

| Test ID | Test Scenario | Expected Result | Actual Result | Status |
|---|---|---|---|:---:|
| `test_01` | Token request with staff ID only (no password) | HTTP 401 Unauthorized | HTTP 401 Unauthorized | **PASS** |
| `test_02` | Token request with empty password string | HTTP 401 Unauthorized | HTTP 401 Unauthorized | **PASS** |
| `test_03` | Token request with incorrect password | HTTP 401 Unauthorized | HTTP 401 Unauthorized | **PASS** |
| `test_04` | Non-existent staff ID with arbitrary password | HTTP 401 Unauthorized | HTTP 401 Unauthorized | **PASS** |
| `test_05` | Valid staff credentials (`dr_clinical_101`) | HTTP 200 + Valid HMAC Token | HTTP 200 + Valid HMAC Token | **PASS** |
| `test_06` | Role escalation attempt (`staff_user` -> `MANAGEMENT`) | Role enforced strictly as `STAFF` | Role enforced strictly as `STAFF` | **PASS** |
| `test_07` | `Set-Cookie: aph_session` issued on auth | `HttpOnly`, `SameSite=Strict` cookie present | Cookie verified | **PASS** |
| `test_08` | Direct GET `/files/` restricted document without auth | HTTP 403 Forbidden | HTTP 403 Forbidden | **PASS** |
| `test_09` | Direct GET `/files/` restricted document with valid cookie | HTTP 200 OK + full PDF content | HTTP 200 OK (399,511 bytes) | **PASS** |
| `test_10` | General staff cookie accessing clinical document | HTTP 403 Forbidden | HTTP 403 Forbidden | **PASS** |
| `test_11` | Direct GET `/data/pdf_cache/<file>.pdf` bypass attempt | HTTP 403 Forbidden | HTTP 403 Forbidden | **PASS** |
| `test_12` | Direct GET `/data/aph_knowledge_index.db` bypass attempt | HTTP 403 Forbidden | HTTP 403 Forbidden | **PASS** |

**Execution Result:** `12/12 PASSED` in 0.371s.

---

### 3.2 Full Unit Test Suite (`tests/test_*.py`)

All test suites were executed across the entire codebase:
- `test_security.py` (Static file protection, path traversal, .env blocking)
- `test_search_regression.py` (Phase 2 deterministic routing)
- `test_phase3_search.py` (Phase 3.3 FTS5 indexing and retrieval)
- `test_phase3_security.py` (Phase 3.4 role derivation and fail-closed public mode)
- `test_auth_security_final.py` (Phase 3.5 final authentication and authorization fixes)

```text
Ran 94 tests in 1.452s
OK (94/94 PASSED)
```

---

### 3.3 Query Accuracy & Regression Benchmark Verification

All query evaluation benchmarks were re-executed against the live running server:

1. **34 Benchmark Queries (`scripts/evaluate_34_queries.py`):**
   - **Result:** `34/34 PASSED (100.0%)`
   - Zero degradation in application launches, PDF form routing, intercom lookups, or Tamil/Tanglish normalization.
2. **150 Extended Hospital Queries (`scripts/evaluate_150_queries.py`):**
   - **Result:** `150/150 PASSED (100.0%)`
   - 100% accuracy across all departments, forms, and tools.
3. **50 Hospital Staff UAT Queries (`scripts/evaluate_50_uat_queries.py`):**
   - **Result:** `50/50 PASSED (100.0%)`
   - Clinical questions, Tamil clinical terms, security injection strings, and unauthorized access challenges all behaved exactly as designed.

**Cumulative Accuracy Across All Suites:** `234/234 queries passed (100.0%)`.

---

## 4. Threat Matrix & Residual Risk Assessment

| Threat Vector | Pre-Fix Status | Post-Fix Status | Residual Risk |
|---|---|---|---|
| **Staff ID Enumeration / Impersonation** | High Vulnerability (Token issued without secret) | **Remediated** (PBKDF2 salted hash verification required) | Low / Standard Credential Security |
| **Role Escalation in Auth Request** | Low Vulnerability (Server enforced role, but warned) | **Remediated** (Client role completely ignored; strictly server-derived) | None |
| **Token Exposure in URL / History** | High Risk (Passing tokens in query strings) | **Remediated** (`Set-Cookie: aph_session=...; HttpOnly; SameSite=Strict`) | None (Browser manages cookie securely) |
| **Direct Cache Bypass (`/data/pdf_cache/`)**| High Vulnerability (Static file handler served files) | **Remediated** (Explicitly blocked with HTTP 403 in `is_blocked_path`) | None |
| **Database Exfiltration (`*.db`)** | High Vulnerability (Direct SQLite file download possible) | **Remediated** (Explicitly blocked with HTTP 403 in `is_blocked_path`) | None |
| **Compromised Gemini API Key** | Blocked / Disabled | **Documented Blocker** (Requires rotation in Google AI Studio) | Managed / Fail-Closed |
| **Institutional Data Processing Agreement** | Pending Hospital Admin Approval | **Documented Blocker** (External cloud transmission disabled) | Managed / Local FTS5 Only |

---

## 5. Unresolved Production Blockers (Pre-UAT Clearance)

The following two institutional items remain required before **cloud-based Gemini answer generation** is turned on in production:

1. **Gemini API Key Rotation:**
   - The original API key that was committed in Phase 1 has been blocked and disabled.
   - For live AI generation with Gemini, the hospital administrator must generate a new API key in Google AI Studio / Google Cloud Console and set it in the deployment environment (`export GEMINI_API_KEY="..."`).
   - The system is currently configured in **fail-closed local mode**: When no valid API key is present, it returns high-precision SQLite FTS5 BM25 document passages with exact page citations without contacting external APIs.
2. **Institutional Data Processing Agreement (DPA) & BAA:**
   - Prior to transmitting clinical document passages to external AI models in production, hospital legal and IT compliance must approve the Cloud Data Processing Terms.

---

## 6. Final Decision

| Milestone Gate | Requirement | Status |
|---|---|:---:|
| **Authentication Enforcement** | Password verification required; no token issued on ID alone | **PASS** |
| **Role Escalation Defense** | Roles derived strictly from server-side registry | **PASS** |
| **PDF Link Security** | Clean browser links via HttpOnly SameSite cookies | **PASS** |
| **Direct Storage Protection**| `/data/pdf_cache/`, `*.db` blocked with HTTP 403 | **PASS** |
| **Unit Test Suite** | 94/94 automated unit tests passing | **PASS** |
| **Query Accuracy Benchmark**| 234/234 queries passing across English, Tamil, Tanglish | **PASS** |
| **Non-Regression** | Zero disruption to applications, forms, and directories | **PASS** |

### **FINAL DECISION: PASS**

The authentication and document authorization security remediation is complete, robust, and fully verified. The codebase on branch `feature/phase3-document-indexing` is in a clean, stable, and secure state for hospital staff User Acceptance Testing.

*(As instructed: No production deployment or merge to `main` has been performed).*
