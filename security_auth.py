#!/usr/bin/env python3
"""
APH SmartSearch AI — Secure Role-Based Authentication & Session Management
Security Specification & Hardening:
1. Rejects and ignores all untrusted client-supplied role headers (X-Staff-Role, X-User-Role).
2. Rejects and ignores all untrusted JSON payload role fields ({"role": "CLINICAL"}).
3. Rejects raw unverified strings (e.g. "Bearer CLINICAL").
4. Derives user role strictly from cryptographically signed HMAC-SHA256 session tokens or verified server sessions.
5. Fails closed to ACCESS_PUBLIC if unauthenticated, invalid, expired, tampered, or revoked.
6. Enforces access levels before database querying, snippet generation, file serving, and LLM transmission.
7. Mandates PBKDF2-HMAC-SHA256 salted password verification; staff ID alone cannot issue tokens.
8. Prevents use of session-signing secret as a login credential; isolates service identities.
9. Implements login rate limiting, brute-force throttling, and account lockout protections.
10. Provides cryptographic token revocation and immediate session termination on logout.
"""

import os
import sys
import time
import json
import hmac
import hashlib
import base64
import secrets
import threading
import sqlite3
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

# Cryptographic Secret Key for Session Token Signing (Strictly for HMAC-SHA256 signing)
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

# Dedicated Internal Service Secret (Completely separate from SESSION_SECRET)
INTERNAL_SERVICE_SECRET = os.environ.get("APH_INTERNAL_SERVICE_SECRET", "").strip()
if not INTERNAL_SERVICE_SECRET:
    _svc_secret_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", ".service_secret")
    if os.path.exists(_svc_secret_file):
        try:
            with open(_svc_secret_file, "r") as _f:
                INTERNAL_SERVICE_SECRET = _f.read().strip()
        except Exception:
            pass
    if not INTERNAL_SERVICE_SECRET:
        INTERNAL_SERVICE_SECRET = secrets.token_hex(32)
        try:
            os.makedirs(os.path.dirname(_svc_secret_file), exist_ok=True)
            with open(_svc_secret_file, "w") as _f:
                _f.write(INTERNAL_SERVICE_SECRET)
            os.chmod(_svc_secret_file, 0o600)
        except Exception:
            pass

# Server-Side Session Store (for stateful session verification)
ACTIVE_SERVER_SESSIONS: Dict[str, Dict[str, Any]] = {}

# Token Revocation Store (Maps signature/token -> expiry timestamp)
_REVOKED_TOKENS: Dict[str, float] = {}

# Rate Limiting & Account Lockout Settings
MAX_LOGIN_ATTEMPTS_PER_IP = 5
IP_RATE_LIMIT_WINDOW_SECONDS = 60
MAX_CONSECUTIVE_STAFF_FAILURES = 5
ACCOUNT_LOCKOUT_DURATION_SECONDS = 900  # 15 minutes lockout

# Thread-safe in-memory tracking
_AUTH_SECURITY_LOCK = threading.Lock()
_IP_ATTEMPT_HISTORY: Dict[str, List[float]] = {}
_STAFF_FAILED_ATTEMPTS: Dict[str, List[float]] = {}
_STAFF_LOCKED_UNTIL: Dict[str, float] = {}


# Cryptographic password hashing and verification helpers
def hash_password(password: str, salt_hex: Optional[str] = None) -> str:
    """Generates a PBKDF2-HMAC-SHA256 salted password hash with 100,000 iterations."""
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


# Narrowly-Scoped Machine-to-Machine Service Identities
# NEVER allow service accounts to masquerade as human clinicians or executives
SERVICE_ACCOUNTS: Dict[str, Dict[str, Any]] = {
    "svc_knowledge_indexer": {
        "role": ACCESS_STAFF,
        "name": "Background Document Indexing Service",
        "description": "Extracts and indexes intranet documents into SQLite FTS5"
    },
    "svc_health_monitor": {
        "role": ACCESS_PUBLIC,
        "name": "Intranet Health Monitor",
        "description": "Periodically monitors health and search status"
    }
}


# Authorized Staff Directory & Role Registry (Server-Side Identity Verification)
# STRICT SECURITY CONTROLS:
# 1. Knowing a valid staff ID alone CANNOT issue an authentication token.
# 2. Every account uses an independent, unique 16-byte cryptographic random salt.
# 3. No plaintext passwords or shared salts exist in the directory.
# 4. Roles are strictly bound server-side; client-supplied role values are discarded.
STAFF_DIRECTORY: Dict[str, Dict[str, Any]] = {
    # Clinical Staff (Doctors & ICU/ER Nurses)
    "dr_clinical_101": {
        "role": ACCESS_CLINICAL,
        "dept": "Emergency Medicine",
        "name": "Dr. S. K. Narayanan",
        "password_hash": "536c0b3b63e08e9cf9630cb9427c1f6b:108354f514bee875d4d1a6e45d3151fa3a2bc2854ed27425e5bc0bf4c825d997"
    },
    "dr_emergency": {
        "role": ACCESS_CLINICAL,
        "dept": "Emergency Medicine",
        "name": "Dr. R. Kavitha",
        "password_hash": "6b42ed674330faf0e778ad3c31f35004:43d8eeda0da63ca9d6e85462ad2f3b836f830f977deedc3db8bef16adc7352c0"
    },
    "dr_shreya": {
        "role": ACCESS_CLINICAL,
        "dept": "Cardiology",
        "name": "Dr. Shreya M.",
        "password_hash": "e79bc7cd2c90cd30848024731b0b0c41:1be914830746a838c72605054b3eb939f8faf1ff3435fba637235c76452bd624"
    },
    "nurse_icu": {
        "role": ACCESS_CLINICAL,
        "dept": "ICU",
        "name": "Staff Nurse Priya",
        "password_hash": "1628f788f5506a34b7a7ccd47ee5767b:6e6c22ce1b588a8a969068ab3cbf01a716e76275a593e9c190d2624425a1e8dd"
    },
    "dr_tamil": {
        "role": ACCESS_CLINICAL,
        "dept": "General Medicine",
        "name": "Dr. Tamilselvan",
        "password_hash": "865351271ebed13340f904f40a0854e1:53834b0d7fdfc1dd5f9bfe8540684ff2a077796850850b3793b4288e30f1398b"
    },

    # General Hospital Staff (Administrative, Nursing, Technicians)
    "staff_user": {
        "role": ACCESS_STAFF,
        "dept": "Administration",
        "name": "A. Murugan",
        "password_hash": "900f12f2fa74a91e58fc5d37af41c4e2:d6f0fb3f80d4cda27264afbfb01922c88ec458f4088bf9371417ce6ff9ea11fa"
    },
    "nurse_john": {
        "role": ACCESS_STAFF,
        "dept": "Ward 3",
        "name": "John Doe",
        "password_hash": "910ecd77c29c46fa451126f470a6959f:f688b1a17aa65ed25592fc9a191a4a2d169507ed5948f73d1863d3c718d03f00"
    },
    "nurse_staff_202": {
        "role": ACCESS_STAFF,
        "dept": "Nursing",
        "name": "Staff Nurse Anitha",
        "password_hash": "d57a23ab6ae8dd183848e41742907990:137ba5c80fef2db938e3909c177ce55b6e5f741caa5a542d73923a99382e1669"
    },
    "nurse_tanglish": {
        "role": ACCESS_STAFF,
        "dept": "OPD",
        "name": "Staff Nurse Deepa",
        "password_hash": "e968a84d5ca38a2aa6c33d134cfb25e8:b4e6ce582a23e0da1eaf69eb4a53209f0d7a1f14826a1d5f2af054f35625353c"
    },
    "test_staff": {
        "role": ACCESS_STAFF,
        "dept": "Testing",
        "name": "Test Staff Account",
        "password_hash": "a25011257dcb370bef0c5a745987ecf1:f15a770ffed362beffada7cd241d8c25db2e33851947b83d1882108dc6d81081"
    },

    # Executive Management (Hospital Board & Administration)
    "admin_mgmt_303": {
        "role": ACCESS_MANAGEMENT,
        "dept": "Hospital Administration",
        "name": "Medical Superintendent",
        "password_hash": "ef41ce936d18276e19c44e9405e5afea:5cc557de4ce8d12309cd323f15ef8f17d3e35bd820b315a1dc62f1c832765002"
    },
    "admin_director": {
        "role": ACCESS_MANAGEMENT,
        "dept": "Executive Office",
        "name": "Managing Director",
        "password_hash": "11737b7fd2e656287412e62f356e3dd8:7c5bf53d15521651aaa8951388eaf114219eb614321a9367ac15a9fb777d496e"
    }
}


def verify_staff_directory_security() -> Dict[str, Any]:
    """
    Audits the STAFF_DIRECTORY to ensure:
    1. No plaintext passwords exist.
    2. Every account has a unique, non-shared salt.
    3. Every account has a valid PBKDF2-HMAC-SHA256 hash.
    4. No two accounts share identical password hashes.
    """
    salts = set()
    hashes = set()
    issues = []
    for uid, entry in STAFF_DIRECTORY.items():
        pw_hash = entry.get("password_hash", "")
        if ":" not in pw_hash:
            issues.append(f"Account {uid} has invalid hash format.")
            continue
        salt, h = pw_hash.split(":", 1)
        if len(salt) < 16:
            issues.append(f"Account {uid} has insufficient salt length.")
        if salt in salts:
            issues.append(f"Account {uid} shares salt with another account.")
        salts.add(salt)
        if h in hashes:
            issues.append(f"Account {uid} shares hash with another account.")
        hashes.add(h)

    return {
        "secure": len(issues) == 0,
        "account_count": len(STAFF_DIRECTORY),
        "unique_salts": len(salts),
        "unique_hashes": len(hashes),
        "issues": issues
    }


# =============================================================================
# RATE LIMITING & ACCOUNT LOCKOUT FUNCTIONS
# =============================================================================

def is_ip_rate_limited(ip_address: str) -> Tuple[bool, int]:
    """Checks if an IP address has exceeded the failed login rate limit."""
    if not ip_address:
        return False, 0
    now = time.time()
    with _AUTH_SECURITY_LOCK:
        history = _IP_ATTEMPT_HISTORY.get(ip_address, [])
        history = [t for t in history if now - t < IP_RATE_LIMIT_WINDOW_SECONDS]
        _IP_ATTEMPT_HISTORY[ip_address] = history
        if len(history) >= MAX_LOGIN_ATTEMPTS_PER_IP:
            retry_after = int(IP_RATE_LIMIT_WINDOW_SECONDS - (now - history[0]))
            return True, max(1, retry_after)
    return False, 0


def is_account_locked(staff_id: str) -> Tuple[bool, int]:
    """Checks if a staff account is locked due to repeated failed logins."""
    if not staff_id:
        return False, 0
    now = time.time()
    with _AUTH_SECURITY_LOCK:
        lock_until = _STAFF_LOCKED_UNTIL.get(staff_id, 0.0)
        if now < lock_until:
            remaining = int(lock_until - now)
            return True, max(1, remaining)
        elif lock_until > 0.0:
            del _STAFF_LOCKED_UNTIL[staff_id]
            _STAFF_FAILED_ATTEMPTS.pop(staff_id, None)
    return False, 0


def record_failed_attempt(ip_address: str, staff_id: str) -> Dict[str, Any]:
    """Records a failed authentication attempt for both IP and staff account."""
    now = time.time()
    with _AUTH_SECURITY_LOCK:
        if ip_address:
            ip_history = _IP_ATTEMPT_HISTORY.setdefault(ip_address, [])
            ip_history.append(now)

        locked = False
        remaining_lockout = 0
        if staff_id:
            staff_history = _STAFF_FAILED_ATTEMPTS.setdefault(staff_id, [])
            staff_history.append(now)
            if len(staff_history) >= MAX_CONSECUTIVE_STAFF_FAILURES:
                _STAFF_LOCKED_UNTIL[staff_id] = now + ACCOUNT_LOCKOUT_DURATION_SECONDS
                locked = True
                remaining_lockout = ACCOUNT_LOCKOUT_DURATION_SECONDS
                print(f"🚨 [SECURITY ALERT] Account '{staff_id}' LOCKED for {ACCOUNT_LOCKOUT_DURATION_SECONDS}s due to {MAX_CONSECUTIVE_STAFF_FAILURES} consecutive failed login attempts.")

        return {
            "account_locked": locked,
            "lockout_seconds": remaining_lockout
        }


def record_successful_login(ip_address: str, staff_id: str):
    """Resets failed attempt counters for the staff account upon successful login."""
    with _AUTH_SECURITY_LOCK:
        if staff_id:
            _STAFF_FAILED_ATTEMPTS.pop(staff_id, None)
            _STAFF_LOCKED_UNTIL.pop(staff_id, None)


def unlock_staff_account(staff_id: str):
    """Administrative unlock of a locked staff account."""
    with _AUTH_SECURITY_LOCK:
        _STAFF_FAILED_ATTEMPTS.pop(staff_id, None)
        _STAFF_LOCKED_UNTIL.pop(staff_id, None)


def reset_rate_limit_tracking():
    """Resets all tracking counters (used in tests and maintenance)."""
    with _AUTH_SECURITY_LOCK:
        _IP_ATTEMPT_HISTORY.clear()
        _STAFF_FAILED_ATTEMPTS.clear()
        _STAFF_LOCKED_UNTIL.clear()


# =============================================================================
# TOKEN REVOCATION & LOGOUT
# =============================================================================

_REVOCATION_DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", ".revoked_tokens.db")

def _init_revocation_db():
    try:
        os.makedirs(os.path.dirname(_REVOCATION_DB), exist_ok=True)
        with sqlite3.connect(_REVOCATION_DB, timeout=5) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS revoked_tokens (
                    token_sig TEXT PRIMARY KEY,
                    exp INTEGER NOT NULL
                )
            """)
            conn.commit()
    except Exception:
        pass

_init_revocation_db()


def revoke_token(token: str) -> bool:
    """Revokes a session token immediately across processes until its expiration time."""
    if not token or not isinstance(token, str):
        return False

    now = int(time.time())
    payload = verify_signed_session_token(token, check_revocation=False)
    exp = int(payload.get("exp", now + 3600)) if payload else now + 3600
    sig = token.rsplit(".", 1)[-1] if "." in token else token

    with _AUTH_SECURITY_LOCK:
        _REVOKED_TOKENS[sig] = float(exp)
        ACTIVE_SERVER_SESSIONS.pop(token, None)

    try:
        with sqlite3.connect(_REVOCATION_DB, timeout=5) as conn:
            conn.execute("INSERT OR REPLACE INTO revoked_tokens (token_sig, exp) VALUES (?, ?)", (sig, exp))
            conn.execute("DELETE FROM revoked_tokens WHERE exp < ?", (now,))
            conn.commit()
    except Exception:
        pass

    return True


def is_token_revoked(token: str) -> bool:
    """Checks if a token has been revoked across processes."""
    if not token or not isinstance(token, str):
        return False
    sig = token.rsplit(".", 1)[-1] if "." in token else token
    now = time.time()
    with _AUTH_SECURITY_LOCK:
        if sig in _REVOKED_TOKENS:
            if _REVOKED_TOKENS[sig] > now:
                return True
            else:
                del _REVOKED_TOKENS[sig]

    try:
        with sqlite3.connect(_REVOCATION_DB, timeout=5) as conn:
            cur = conn.execute("SELECT exp FROM revoked_tokens WHERE token_sig = ?", (sig,))
            row = cur.fetchone()
            if row and row[0] > now:
                with _AUTH_SECURITY_LOCK:
                    _REVOKED_TOKENS[sig] = float(row[0])
                return True
    except Exception:
        pass

    return False


def build_session_cookie(
    token: str,
    is_https: bool = False,
    max_age: int = 3600,
    samesite: str = "Lax"
) -> str:
    """
    Builds a secure session cookie string.
    Uses HttpOnly to prevent XSS exfiltration.
    Uses SameSite=Lax (or configured) to allow seamless top-level browser link navigation across hosts.
    Appends Secure when transport is HTTPS or when HTTPS is enforced.
    """
    parts = [
        f"aph_session={token}",
        "Path=/",
        f"Max-Age={max_age}",
        "HttpOnly",
        f"SameSite={samesite}"
    ]
    if is_https:
        parts.append("Secure")
    return "; ".join(parts)


def build_logout_cookie(
    is_https: bool = False,
    samesite: str = "Lax"
) -> str:
    """Builds an immediately expired cookie header to clear browser session."""
    parts = [
        "aph_session=",
        "Path=/",
        "Expires=Thu, 01 Jan 1970 00:00:00 GMT",
        "Max-Age=0",
        "HttpOnly",
        f"SameSite={samesite}"
    ]
    if is_https:
        parts.append("Secure")
    return "; ".join(parts)


# =============================================================================
# AUTHENTICATION & TOKEN ISSUANCE
# =============================================================================

def authenticate_and_issue_staff_token(
    staff_id: str,
    password: Optional[str] = None
) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Verifies staff identity and credentials server-side before issuing signed session tokens.
    STRICT SECURITY RULES:
    1. Knowing a valid staff ID alone CANNOT issue an authentication token.
    2. Requires valid verified password.
    3. Session-signing secrets and service keys CANNOT be used to authenticate human staff accounts.
    4. Never permits client-selected roles; roles are derived strictly from internal registry.
    Returns: (is_authenticated, token_or_error_msg, assigned_role, staff_name)
    """
    clean_id = staff_id.strip() if staff_id else ""
    if not clean_id:
        return False, "Authentication failed: Staff ID is required.", None, None

    staff_entry = STAFF_DIRECTORY.get(clean_id)
    if not staff_entry:
        return False, f"Authentication failed: Staff ID '{clean_id}' is not recognized in hospital staff directory.", None, None

    clean_pw = password.strip() if password else ""
    if not clean_pw:
        return False, "Authentication failed: Password is required. Knowing a staff ID alone cannot issue an authentication token.", None, None

    # CRITICAL: Prevent using session-signing secret as an authentication credential!
    if SESSION_SECRET and hmac.compare_digest(clean_pw, SESSION_SECRET):
        print(f"🚨 [SECURITY AUDIT] Attempted use of session-signing secret as staff login password for '{clean_id}' rejected!")
        return False, "Authentication failed: Session secret cannot be used as an authentication credential.", None, None

    # CRITICAL: Prevent using internal service secret as a staff password!
    if INTERNAL_SERVICE_SECRET and hmac.compare_digest(clean_pw, INTERNAL_SERVICE_SECRET):
        print(f"🚨 [SECURITY AUDIT] Attempted use of internal service secret as staff login password for '{clean_id}' rejected!")
        return False, "Authentication failed: Service keys cannot be used to authenticate human staff accounts.", None, None

    stored_hash = staff_entry.get("password_hash", "")
    if not stored_hash or not verify_password(clean_pw, stored_hash):
        return False, "Authentication failed: Invalid staff password or unauthorized credentials.", None, None

    assigned_role = staff_entry["role"]
    staff_name = staff_entry.get("name", "Hospital Staff")

    token = create_signed_session_token(clean_id, assigned_role)
    return True, token, assigned_role, staff_name


def authenticate_service_identity(
    service_id: str,
    service_key: str
) -> Tuple[bool, Optional[str], Optional[str], Optional[str]]:
    """
    Authenticates dedicated machine-to-machine service identities with narrowly-scoped roles.
    STRICT SECURITY CONTROLS:
    1. Rejects any attempt to use SESSION_SECRET as a service key.
    2. Compares service_key strictly against INTERNAL_SERVICE_SECRET using constant-time comparison.
    3. Rejects any service_id not registered in SERVICE_ACCOUNTS.
    4. NEVER allows a service identity to claim clinical or management privileges.
    5. Returns: (is_authenticated, token_or_err, assigned_role, service_name)
    """
    clean_id = service_id.strip() if service_id else ""
    if not clean_id:
        return False, "Authentication failed: Service ID is required.", None, None

    svc_entry = SERVICE_ACCOUNTS.get(clean_id)
    if not svc_entry:
        return False, f"Authentication failed: Service ID '{clean_id}' is not a recognized internal service.", None, None

    clean_key = service_key.strip() if service_key else ""
    if not clean_key:
        return False, "Authentication failed: Service key is required.", None, None

    # CRITICAL: Prevent using SESSION_SECRET as a service key!
    if SESSION_SECRET and hmac.compare_digest(clean_key, SESSION_SECRET):
        print(f"🚨 [SECURITY AUDIT] Attempted use of session-signing secret as service key rejected!")
        return False, "Authentication failed: Session secret cannot be used as an authentication credential.", None, None

    # Verify against dedicated INTERNAL_SERVICE_SECRET
    if not INTERNAL_SERVICE_SECRET or not hmac.compare_digest(clean_key, INTERNAL_SERVICE_SECRET):
        return False, "Authentication failed: Invalid service key.", None, None

    assigned_role = svc_entry["role"]
    service_name = svc_entry.get("name", "Internal Service")
    token = create_signed_session_token(clean_id, assigned_role, duration_seconds=1800)
    return True, token, assigned_role, service_name


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
    secret: str = SESSION_SECRET,
    check_revocation: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Cryptographically verifies an HMAC-SHA256 session token.
    Returns decoded payload if valid, unexpired, and not revoked; returns None otherwise.
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

        # Check token revocation
        if check_revocation and is_token_revoked(token):
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
        print("🛡️ [SECURITY AUDIT] Blocked unverified role escalation attempt. Request enforced as PUBLIC.")

    # 4. Default: Unauthenticated public request
    return (ACCESS_PUBLIC, None)
