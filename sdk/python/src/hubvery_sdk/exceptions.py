"""Exceptions raised by the HUBVERY SDK."""

from __future__ import annotations

from .models import Error


class HubveryAPIError(Exception):
    """Raised when the HUBVERY API returns an RFC 7807 problem+json error."""

    def __init__(self, error: Error) -> None:
        self.error = error
        self.status = error.status
        self.title = error.title
        self.detail = error.detail
        self.code = error.code
        super().__init__(f"{error.status} {error.title}: {error.detail or ''}".strip())


class HubveryAuthError(Exception):
    """Raised when OAuth2 client credentials cannot be exchanged for a token."""
