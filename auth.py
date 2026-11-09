"""Authentication and role-permission checks for AURORA.

Passwords use PBKDF2-HMAC-SHA256. The demo credentials in the SQL seed are
for classroom demonstration only and should be changed before real use.
"""
import hashlib
import hmac

from db import execute, fetch_one

PBKDF2_ITERATIONS = 310_000


def verify_password(password, salt, expected_hash):
    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"),
        PBKDF2_ITERATIONS,
    ).hex()
    return hmac.compare_digest(actual, expected_hash)


def authenticate(username, password):
    """Return a minimal authenticated user record, or None."""
    user = fetch_one(
        """SELECT u.user_id, u.username, u.password_hash, u.password_salt,
                  u.is_active, r.role_code, r.role_name
           FROM app_user u
           JOIN app_role r ON r.role_id = u.role_id
           WHERE u.username = %s""",
        (username.strip(),),
    )
    if not user or not user["is_active"]:
        return None
    if not verify_password(password, user["password_salt"], user["password_hash"]):
        return None
    execute("UPDATE app_user SET last_login_at = CURRENT_TIMESTAMP WHERE user_id = %s",
            (user["user_id"],))
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "role_code": user["role_code"],
        "role_name": user["role_name"],
    }


def has_permission(user, permission_code):
    """Resolve permissions through role_permission; deny by default."""
    if not user:
        return False
    result = fetch_one(
        """SELECT 1 AS allowed
           FROM app_user u
           JOIN role_permission rp ON rp.role_id = u.role_id
           JOIN app_permission p ON p.permission_id = rp.permission_id
           WHERE u.user_id = %s AND u.is_active = 1 AND p.permission_code = %s""",
        (user["user_id"], permission_code),
    )
    return result is not None


def require_permission(user, permission_code):
    if not has_permission(user, permission_code):
        raise PermissionError(f"Account is not authorized for: {permission_code}")
