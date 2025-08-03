import os
import secrets
import hmac
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "secret")

_bearer_scheme = HTTPBearer(auto_error=False)
_token: str | None = None
_session_key = "admin_authenticated"

def _verify_credentials(username: str, password: str) -> bool:
    return hmac.compare_digest(username, ADMIN_USERNAME) and hmac.compare_digest(password, ADMIN_PASSWORD)

def authenticate(request: Request, username: str, password: str, use_token: bool) -> dict:
    global _token
    if not _verify_credentials(username, password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="invalid credentials")
    if use_token:
        _token = secrets.token_urlsafe(32)
        return {"token": _token}
    request.session[_session_key] = True
    return {"status": "ok"}

def require_admin(
    request: Request,
    creds: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
):
    if request.session.get(_session_key):
        return True
    if creds and creds.scheme.lower() == "bearer" and _token and hmac.compare_digest(creds.credentials, _token):
        return True
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="not authenticated")
