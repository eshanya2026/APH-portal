#!/usr/bin/env python3
"""
APH SmartSearch AI — Secure Role-Based Authentication & Session Management
Security Specification:
1. Rejects and ignores all untrusted client-supplied role headers (X-Staff-Role, X-User-Role).
2. Rejects and ignores all untrusted JSON payload role fields ({"role": "CLINICAL"}).
3. Rejects raw unverified strings (e.g. "Bearer CLINICAL").
4. Derives user role strictly from cryptographically signed HMAC-SHA256 session tokens or verified server sessions.
5. Fails closed to ACCESS_PUBLIC if unauthenticated, invalid, expired, or tampered.
6. Enforces access levels before database querying, snippet generation, and LLM transmission.
"""

import os
import sys
import time
import json
import hmac
import hashlib
import base64
import secrets
from typing import Dict, Any, Optional, Tuple, List

# Access Levels
ACCESS_PUBLIC = "PUBLIC"
ACCESS_STAFF = "STAFF"
ACCESS_CLINICAL = "CLINICAL"
ACCESS_MANAGEMENT = "MANAGEMENT"

VALID_ROLES = {ACCESS_PUBLIC, ACCESS_STAFF, ACCESS_CLINICAL, ACCESS_MANAGEMENT}

ROLE_PERMISSIONS: Dict[str, List[str]] = {
    ACCESS_PUBLIC: [ACCESS_PUBLIC],
    ACCESS_STAFF: [ACCESS_PUBLIC, ACCESS_STAFF],
    ACCESS_CLINICAL: [ACCESS_PUBLIC, ACCESS_STAFF, ACCESS_CLINICAL],
    ACCESS_MANAGEMENT: [ACCESS_PUBLIC, ACCESS_STAFF, ACCESS_CLINICAL, ACCESS_MANAGEMENT],
}

# Cryptographic Secret Key for Session Token Signing
SESSION_SECRET = os.environ.get("APH_SESSION_SECRET", "").strip()
if not SESSION_SECRET:
    _secret_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", ".session_secret")
    if os.path.exists(_secret_file):
        try:
            with open(_secret_file, "r") as _f:
                SESSION_SECRET = _f.read().strip()
        except Exception:
            pass
    if not SESSION_SECRET:
        SESSION_SECRET = secrets.token_hex(32)
        try:
            os.makedirs(os.path.dirname(_secret_file), exist_ok=True)
            with open(_secret_file, "w") as _f:
                _f.write(SESSION_SECRET)
            os.chmod(_secret_file, 0o600)
        except Exception:
            pass

# Server-Side Session Store (for stateful session verification)
ACTIVE_SERVER_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Cryptographic password hashing and verification helpers
def hash_password(password: str, salt_hex: Optional[str] = None) -> str:
    """Generates a PBKDF2-HMAC-SHA256 salted password hash."""
    if salt_hex:
        salt = bytes.fromhex(salt_hex)
    else:
        salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return f"{salt.hex()}:{derived.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    """Constant-time verification of password against stored PBKDF2 hash."""
    if not password or not stored_hash or ":" not in stored_hash:
        return False
    try:
        salt_hex, key_hex = stored_hash.split(":", 1)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(key_hex)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


# Authorized Staff Directory & Role Registry (Server-Side Identity Verification)
# STRICT SECURITY REQUIREMENT:
# Knowing a valid staff ID alone CANNOT issue an authentication token.
# Every staff account requires a verified password or institutional auth credential.
# Roles are derived strictly from this internal registry; client-supplied roles are ignored.
STAFF_DIRECTORY: Dict[str, Dict[str, Any]] = {
    # Clinical Staff (Doctors & ICU/ER Nurses)
    "dr_clinical_101": {
        "role": ACCESS_CLINICAL,
        "dept": "Emergency Medicine",
        "name": "Dr. S. K. Narayanan",
        "password_hash": "0123456789abcdef0123456789abcdef:a6e98aa6c169bdbccfedd2f63fa154379f9fce9445ae3175ee650b1573c7ca6c"  # Clinical#2026!
    },
    "dr_emergency": {
        "role": ACCESS_CLINICAL,
        "dept": "Emergency Medicine",
        "name": "Dr. R. Kavitha",
        "password_hash": "0123456789abcdef0123456789abcdef:da3288936fa873a72a2396c0a2cf67cdc4ef94dff63bbe206f2abcd2f9b79d8c"  # Emergency#2026!
    },
    "dr_shreya": {
        "role": ACCESS_CLINICAL,
        "dept": "Cardiology",
        "name": "Dr. Shreya M.",
        "password_hash": "0123456789abcdef0123456789abcdef:d23dc9bd8452aa2aa730f8a76d6e1e12d9c992986e184d1afbb6aee40162cb50"  # ShreyaMed#2026!
    },
    "nurse_icu": {
        "role": ACCESS_CLINICAL,
        "dept": "ICU",
        "name": "Staff Nurse Priya",
        "password_hash": "0123456789abcdef0123456789abcdef:29c4865b2eb38ce113bd113e8196000b260e6a47ac0a0efdff3ce979b50172d2"  # IcuNurse#2026!
    },
    "dr_tamil": {
        "role": ACCESS_CLINICAL,
        "dept": "General Medicine",
        "name": "Dr. Tamilselvan",
        "password_hash": "0123456789abcdef0123456789abcdef:0396c06d893241ae98c3fc7c004a63765a4684979183fda45eaa50f36633dad2"  # TamilDoc#2026!
    },

    # General Hospital Staff (Administrative, Nursing, Technicians)
    "staff_user": {
        "role": ACCESS_STAFF,
        "dept": "Administration",
        "name": "A. Murugan",
        "password_hash": "0123456789abcdef0123456789abcdef:4dd7b82fbc0b6961df14e545c46849bd743c91a16c2e6d48dd16c2fa9bda1e4d"  # StaffUser#2026!
    },
    "nurse_john": {
        "role": ACCESS_STAFF,
        "dept": "Ward 3",
        "name": "John Doe",
        "password_hash": "0123456789abcdef0123456789abcdef:0549041c427b80226f250f76fcb1817201fbfab1c725b5428a731d244d15a5b9"  # NurseJohn#2026!
    },
    "nurse_staff_202": {
        "role": ACCESS_STAFF,
        "dept": "Nursing",
        "name": "Staff Nurse Anitha",
        "password_hash": "0123456789abcdef0123456789abcdef:bad7eb4a246bdb207c61a1bea5ff80b450084738769685ae03b83a1720761d3c"  # Nurse202#2026!
    },
    "nurse_tanglish": {
        "role": ACCESS_STAFF,
        "dept": "OPD",
        "name": "Staff Nurse Deepa",
        "password_hash": "0123456789abcdef0123456789abcdef:8b9b2f3aa0866208363f1ff06c267fbd8726e6521586eac0856b25cfd256d0ca"  # TanglishNurse#2026!
    },
    "test_staff": {
        "role": ACCESS_STAFF,
        "dept": "Testing",
        "name": "Test Staff Account",
        "password_hash": "0123456789abcdef0123456789abcdef:8c48aa444a884a795b92a556427d8f065df3cc5beec08916c015725af835c01e"  # TestStaff#2026!
    },

    # Executive Management (Hospital Board & Administration)
    "admin_mgmt_303": {
        "role": ACCESS_MANAGEMENT,
        "dept": "Hospital Administration",
        "name": "Medical Superintendent",
        "password_hash": "0123456789abcdef0123456789abcdef:777054fd574605fc2b1077cb1740c08bdd953794b98f5d7df8e8b9fdca8b9866"  # HospitalAdmin#2026!
    },
    "admin_director": {
        "role": ACCESS_MANAGEMENT,
        "dept": "Executive Office",
        "name": "Managing Director",
        "password_hash": "0123456789abcdef0123456789abcdef:ec69621be96a53dceb95ef86ac08fcb952e76bb0fd5be06c04ce8a6b2f78c1d1"  # DirectorMgmt#2026!
    }
}


def authenticate_and_issue_staff_token(
    staff_id: str,
    password: Optional[str] = None,
    service_key: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Verifies staff identity and credentials server-side before issuing signed session tokens.
    STRICT SECURITY RULES:
    1. Knowing a valid staff ID alone CANNOT issue an authentication token.
    2. Requires valid verified password or trusted internal service key.
    3. Never permits client-selected roles; roles are derived strictly from internal registry.
    Returns: (is_authenticated, token_or_error_msg, assigned_role, staff_name)
    """
    clean_id = staff_id.strip() if staff_id else ""
    if not clean_id:
        return False, "Authentication failed: Staff ID is required.", None, None

    staff_entry = STAFF_DIRECTORY.get(clean_id)
    if not staff_entry:
        return False, f"Authentication failed: Staff ID '{clean_id}' is not recognized in hospital staff directory.", None, None

    # Check for trusted machine-to-machine internal service key
    is_trusted_service = False
    if service_key and isinstance(service_key, str) and SESSION_SECRET:
        if hmac.compare_digest(service_key.strip(), SESSION_SECRET):
            is_trusted_service = True

    if not is_trusted_service:
        clean_pw = password.strip() if password else ""
        if not clean_pw:
            return False, "Authentication failed: Password is required. Knowing a staff ID alone cannot issue an authentication token.", None, None

        stored_hash = staff_entry.get("password_hash", "")
        if not stored_hash or not verify_password(clean_pw, stored_hash):
            return False, "Authentication failed: Invalid staff password or unauthorized credentials.", None, None

    assigned_role = staff_entry["role"]
    staff_name = staff_entry.get("name", "Hospital Staff")

    token = create_signed_session_token(clean_id, assigned_role)
    return True, token, assigned_role, staff_name


def create_signed_session_token(
    staff_id: str,
    role: str,
    duration_seconds: int = 3600,
    secret: str = SESSION_SECRET
) -> str:
    """
    Creates an HMAC-SHA256 signed session token for verified hospital staff.
    Format: aph_s_<base64_payload>.<hmac_hex_sig>
    """
    role = role.upper().strip()
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid hospital role: {role}")

    now = int(time.time())
    payload = {
        "sub": staff_id,
        "role": role,
        "iat": now,
        "exp": now + duration_seconds,
        "nonce": secrets.token_hex(8)
    }
    payload_json = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    b64_payload = base64.urlsafe_b64encode(payload_json).decode('utf-8')
    signature = hmac.new(secret.encode('utf-8'), b64_payload.encode('utf-8'), hashlib.sha256).hexdigest()

    token = f"aph_s_{b64_payload}.{signature}"
    return token


def verify_signed_session_token(
    token: str,
    secret: str = SESSION_SECRET
) -> Optional[Dict[str, Any]]:
    """
    Cryptographically verifies an HMAC-SHA256 session token.
    Returns decoded payload if valid and unexpired; returns None otherwise.
    """
    if not token or not isinstance(token, str) or not token.startswith("aph_s_"):
        return None

    try:
        raw = token[len("aph_s_"):]
        if "." not in raw:
            return None
        b64_payload, signature = raw.rsplit(".", 1)

        expected_sig = hmac.new(secret.encode('utf-8'), b64_payload.encode('utf-8'), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            # Signature mismatch: token tampered or signed with different key
            return None

        # Decode and parse payload
        payload_bytes = base64.urlsafe_b64decode(b64_payload.encode('utf-8'))
        payload = json.loads(payload_bytes.decode('utf-8'))

        # Check expiration
        now = int(time.time())
        if payload.get("exp", 0) < now:
            return None

        # Check role validity
        role = payload.get("role")
        if role not in VALID_ROLES:
            return None

        return payload
    except Exception:
        return None


def create_server_session(
    staff_id: str,
    role: str,
    duration_seconds: int = 3600
) -> str:
    """
    Creates a server-side session in ACTIVE_SERVER_SESSIONS.
    Returns secure opaque session ID.
    """
    role = role.upper().strip()
    if role not in VALID_ROLES:
        raise ValueError(f"Invalid hospital role: {role}")

    session_id = f"sess_{secrets.token_urlsafe(32)}"
    now = int(time.time())
    ACTIVE_SERVER_SESSIONS[session_id] = {
        "staff_id": staff_id,
        "role": role,
        "iat": now,
        "exp": now + duration_seconds
    }
    return session_id


def verify_server_session(session_id: str) -> Optional[Dict[str, Any]]:
    """Verifies a server-side session from the active registry."""
    if not session_id or not isinstance(session_id, str):
        return None

    sess = ACTIVE_SERVER_SESSIONS.get(session_id)
    if not sess:
        return None

    if sess.get("exp", 0) < int(time.time()):
        del ACTIVE_SERVER_SESSIONS[session_id]
        return None

    return sess


def extract_verified_role(
    headers: Any,
    body_dict: Optional[Dict[str, Any]] = None
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Strictly extracts and validates user role from incoming HTTP request.
    SECURITY AUDIT RULES:
    1. NEVER trusts 'X-Staff-Role', 'X-User-Role', or other custom role headers.
    2. NEVER trusts 'role' or 'user_role' fields in JSON request payload.
    3. Rejects raw strings like 'Bearer CLINICAL'.
    4. Only validates cryptographically signed session tokens or active server sessions.
    5. Returns (verified_role, session_metadata). Defaults safely to (ACCESS_PUBLIC, None).
    """
    # 1. Parse candidate token from Authorization header or Cookie or X-Session-Token
    auth_header = ""
    cookie_header = ""
    session_token_header = ""

    if hasattr(headers, "get"):
        auth_header = headers.get("Authorization", "") or ""
        cookie_header = headers.get("Cookie", "") or ""
        session_token_header = headers.get("X-Session-Token", "") or ""
    elif isinstance(headers, dict):
        auth_header = headers.get("Authorization") or headers.get("authorization") or ""
        cookie_header = headers.get("Cookie") or headers.get("cookie") or ""
        session_token_header = headers.get("X-Session-Token") or headers.get("x-session-token") or ""

    candidate_token = ""

    # Check Authorization: Bearer <token>
    if auth_header:
        parts = auth_header.strip().split()
        if len(parts) == 2 and parts[0].lower() in ["bearer", "token"]:
            candidate_token = parts[1].strip()

    # Check Cookie: aph_session=<token>
    if not candidate_token and cookie_header:
        for item in cookie_header.split(";"):
            item = item.strip()
            if item.startswith("aph_session="):
                candidate_token = item.split("=", 1)[1].strip()
                break

    # Check X-Session-Token: <token>
    if not candidate_token and session_token_header:
        candidate_token = session_token_header.strip()

    # 2. Check signed token
    if candidate_token:
        # A. Verify HMAC-SHA256 signed token
        signed_payload = verify_signed_session_token(candidate_token)
        if signed_payload:
            return (signed_payload["role"], signed_payload)

        # B. Verify server-side registered session
        server_sess = verify_server_session(candidate_token)
        if server_sess:
            return (server_sess["role"], server_sess)

    # 3. Detect and log any spoofing attempt
    has_spoofed_hdr = bool(
        (hasattr(headers, "get") and (headers.get("X-Staff-Role") or headers.get("X-User-Role"))) or
        (isinstance(headers, dict) and (headers.get("X-Staff-Role") or headers.get("X-User-Role")))
    )
    has_spoofed_body = bool(isinstance(body_dict, dict) and (body_dict.get("role") or body_dict.get("user_role")))
    if has_spoofed_hdr or has_spoofed_body:
        # Security log: unauthorized role escalation attempt blocked
        print("🛡️ [SECURITY AUDIT] Blocked unverified role escalation attempt. Request enforced as PUBLIC.")

    # 4. Default: Unauthenticated public request
    return (ACCESS_PUBLIC, None)
