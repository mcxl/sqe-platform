"""Phase 6A — Separate fictional client identity.

Uses HTTP Basic with environment-configured credentials.
One identity, one engagement.  No default password, no hard-coded credential.
"""

from __future__ import annotations

import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

basic_auth = HTTPBasic(auto_error=False)


def require_client(
    credentials: HTTPBasicCredentials | None = Security(basic_auth),
) -> str:
    """Return the configured engagement ID for an authenticated fictional client.

    Reads ``ACE_CLIENT_USERNAME``, ``ACE_CLIENT_PASSWORD``, and
    ``ACE_CLIENT_ENGAGEMENT_ID`` from the environment.
    Fails closed (503) when configuration is missing.
    Returns a generic 403 for any authentication failure.
    """
    username = os.environ.get("ACE_CLIENT_USERNAME")
    password = os.environ.get("ACE_CLIENT_PASSWORD")
    engagement_id = os.environ.get("ACE_CLIENT_ENGAGEMENT_ID")

    # Fail closed when configuration is missing (empty strings included)
    if not username or not password or not engagement_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Client access not configured",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    # Constant-time comparison
    if not secrets.compare_digest(credentials.username or "", username):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )
    if not secrets.compare_digest(credentials.password or "", password):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied",
        )

    return engagement_id
