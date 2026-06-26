from __future__ import annotations

import json
import os
from typing import Annotated, Callable
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient, PyJWKSet

from .config import Settings
from .models import AuthenticatedUser


_bearer = HTTPBearer(auto_error=False)


class SupabaseTokenVerifier:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        static_jwks_json = os.getenv("SUPABASE_JWKS_JSON", "").strip()
        if static_jwks_json:
            # Use static JWKS when container has no outbound internet access
            self._static_jwks = PyJWKSet.from_dict(json.loads(static_jwks_json))
            self._jwks_client = None
        else:
            self._static_jwks = None
            self._jwks_client = PyJWKClient(settings.jwks_url, cache_keys=True, lifespan=3600)

    def _get_signing_key(self, token: str) -> jwt.PyJWK:
        if self._static_jwks is not None:
            header = jwt.get_unverified_header(token)
            kid = header.get("kid")
            for key in self._static_jwks.keys:
                if key.key_id == kid:
                    return key
            raise jwt.exceptions.PyJWKSetError(f"Unable to find key: {kid}")
        return self._jwks_client.get_signing_key_from_jwt(token)  # type: ignore[union-attr]

    def verify(self, token: str) -> AuthenticatedUser:
        try:
            signing_key = self._get_signing_key(token)
            claims = jwt.decode(
                token,
                signing_key.key,
                algorithms=["ES256", "RS256"],
                audience=self._settings.jwt_audience,
                issuer=self._settings.jwt_issuer,
                options={"require": ["exp", "sub", "aud", "iss"]},
            )
            user_id = UUID(str(claims["sub"]))
            email = str(claims.get("email") or "").strip().lower()
            if not email:
                raise ValueError("email claim is missing")
            return AuthenticatedUser(id=user_id, email=email)
        except (jwt.PyJWTError, KeyError, TypeError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired access token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from None


def create_current_user_dependency(
    verifier: SupabaseTokenVerifier,
) -> Callable[..., AuthenticatedUser]:
    def current_user(
        credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
    ) -> AuthenticatedUser:
        if credentials is None or credentials.scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Bearer access token is required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return verifier.verify(credentials.credentials)

    return current_user
