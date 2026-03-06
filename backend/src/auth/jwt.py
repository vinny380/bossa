"""Verify Supabase JWT for control plane auth."""

import jwt
from jwt import (ExpiredSignatureError, InvalidAudienceError,
                 InvalidSignatureError, PyJWKClient, PyJWTError)
from src.config import settings


def _get_issuer() -> str | None:
    if not settings.supabase_url:
        return None
    base = settings.supabase_url.rstrip("/")
    return f"{base}/auth/v1"


def verify_supabase_jwt(token: str) -> dict:
    """Verify Supabase JWT and return claims. Raises ValueError if invalid."""
    issuer = _get_issuer()
    if not issuer:
        raise ValueError("SUPABASE_URL required for JWT verification")

    def _raise(err: Exception) -> None:
        if isinstance(err, ExpiredSignatureError):
            raise ValueError("Token expired. Run 'bossa login' again.") from None
        if isinstance(err, InvalidSignatureError):
            raise ValueError(
                "Invalid token signature. Check SUPABASE_JWT_SECRET matches your Supabase project."
            ) from None
        if isinstance(err, InvalidAudienceError):
            raise ValueError("Invalid token audience.") from None
        raise ValueError("Invalid or expired token") from err

    # 1. Try JWKS (Supabase JWT Signing Keys - ES256, RS256)
    #    Works for projects that migrated from legacy JWT secret
    try:
        jwks_url = f"{issuer}/.well-known/jwks.json"
        jwks = PyJWKClient(jwks_url)
        signing_key = jwks.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token,
            signing_key.key,
            audience="authenticated",
            algorithms=["RS256", "ES256"],
            issuer=issuer,
        )
        return payload
    except PyJWTError as e:
        # 2. Fall back to legacy JWT secret (HS256)
        #    For projects that haven't migrated to signing keys
        if settings.supabase_jwt_secret:
            try:
                payload = jwt.decode(
                    token,
                    settings.supabase_jwt_secret,
                    audience="authenticated",
                    algorithms=["HS256"],
                    issuer=issuer,
                    options={"verify_iss": True},
                )
                return payload
            except PyJWTError as e2:
                _raise(e2)
        _raise(e)
