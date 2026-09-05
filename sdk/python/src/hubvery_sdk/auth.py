"""OAuth2 client credentials flow for the HUBVERY API.

Implemented as an explicit token manager rather than an httpx.Auth
subclass, so the refresh logic and expiry buffer stay simple and
easy to unit test in isolation.
"""

from __future__ import annotations

import time
from typing import Optional

import httpx

from .exceptions import HubveryAuthError

DEFAULT_TOKEN_URL = "https://auth.hubvery.com/oauth/token"


class TokenManager:
    def __init__(
        self,
        client_id: str,
        client_secret: str,
        scopes: list[str],
        token_url: str = DEFAULT_TOKEN_URL,
    ) -> None:
        self._client_id = client_id
        self._client_secret = client_secret
        self._scopes = scopes
        self._token_url = token_url
        self._access_token: Optional[str] = None
        self._expires_at: float = 0.0

    def _token_is_valid(self) -> bool:
        # 30 second buffer before expiry to avoid using a token that
        # expires mid-request.
        return self._access_token is not None and time.time() < self._expires_at - 30

    def get_token_sync(self, client: httpx.Client) -> str:
        if self._token_is_valid():
            return self._access_token  # type: ignore[return-value]
        response = client.post(
            self._token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": " ".join(self._scopes),
            },
        )
        return self._parse_token_response(response)

    async def get_token_async(self, client: httpx.AsyncClient) -> str:
        if self._token_is_valid():
            return self._access_token  # type: ignore[return-value]
        response = await client.post(
            self._token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": " ".join(self._scopes),
            },
        )
        return self._parse_token_response(response)

    def _parse_token_response(self, response: httpx.Response) -> str:
        if response.status_code != 200:
            raise HubveryAuthError(
                f"Token request failed: {response.status_code} {response.text}"
            )
        payload = response.json()
        try:
            access_token = payload["access_token"]
            expires_in = payload.get("expires_in", 3600)
        except KeyError as exc:
            raise HubveryAuthError(
                f"Token response missing 'access_token': {payload}"
            ) from exc
        self._access_token = access_token
        self._expires_at = time.time() + expires_in
        return access_token
