"""Sync and async clients for the HUBVERY Fleet API.

Covers the five operations defined in spec/openapi.yaml: getHealth,
listCapabilities, registerCapability, getCapability, submitTask,
and getTask.
"""

from __future__ import annotations

from typing import Any

import httpx

from .auth import TokenManager
from .exceptions import HubveryAPIError
from .models import CapabilityManifest, Error, Task, TaskRequest

DEFAULT_BASE_URL = "https://api.hubvery.com/v0"


def _raise_for_problem_json(response: httpx.Response) -> None:
    if response.status_code >= 400:
        try:
            error = Error.model_validate(response.json())
        except Exception:
            response.raise_for_status()
            return
        raise HubveryAPIError(error)


class HubveryClient:
    """Synchronous client."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = DEFAULT_BASE_URL,
        scopes: list[str] | None = None,
    ) -> None:
        self._http = httpx.Client(base_url=base_url)
        self._tokens = TokenManager(
            client_id, client_secret, scopes or ["tasks:submit", "tasks:read"]
        )

    def _headers(self) -> dict[str, str]:
        token = self._tokens.get_token_sync(self._http)
        return {"Authorization": f"Bearer {token}"}

    def get_health(self) -> dict[str, Any]:
        response = self._http.get("/health")
        _raise_for_problem_json(response)
        return response.json()

    def list_capabilities(self) -> list[CapabilityManifest]:
        response = self._http.get("/capabilities", headers=self._headers())
        _raise_for_problem_json(response)
        items = response.json()["items"]
        return [CapabilityManifest.model_validate(item) for item in items]

    def register_capability(self, manifest: CapabilityManifest) -> CapabilityManifest:
        response = self._http.post(
            "/capabilities",
            json=manifest.model_dump(exclude_none=True),
            headers=self._headers(),
        )
        _raise_for_problem_json(response)
        return CapabilityManifest.model_validate(response.json())

    def get_capability(self, capability_id: str) -> CapabilityManifest:
        response = self._http.get(
            f"/capabilities/{capability_id}", headers=self._headers()
        )
        _raise_for_problem_json(response)
        return CapabilityManifest.model_validate(response.json())

    def submit_task(self, task_request: TaskRequest) -> Task:
        response = self._http.post(
            "/tasks",
            json=task_request.model_dump(exclude_none=True),
            headers=self._headers(),
        )
        _raise_for_problem_json(response)
        return Task.model_validate(response.json())

    def get_task(self, task_id: str) -> Task:
        response = self._http.get(f"/tasks/{task_id}", headers=self._headers())
        _raise_for_problem_json(response)
        return Task.model_validate(response.json())

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "HubveryClient":
        return self

    def __exit__(self, *exc_info: object) -> None:
        self.close()


class AsyncHubveryClient:
    """Async client, same operations as HubveryClient."""

    def __init__(
        self,
        client_id: str,
        client_secret: str,
        base_url: str = DEFAULT_BASE_URL,
        scopes: list[str] | None = None,
    ) -> None:
        self._http = httpx.AsyncClient(base_url=base_url)
        self._tokens = TokenManager(
            client_id, client_secret, scopes or ["tasks:submit", "tasks:read"]
        )

    async def _headers(self) -> dict[str, str]:
        token = await self._tokens.get_token_async(self._http)
        return {"Authorization": f"Bearer {token}"}

    async def get_health(self) -> dict[str, Any]:
        response = await self._http.get("/health")
        _raise_for_problem_json(response)
        return response.json()

    async def list_capabilities(self) -> list[CapabilityManifest]:
        response = await self._http.get("/capabilities", headers=await self._headers())
        _raise_for_problem_json(response)
        items = response.json()["items"]
        return [CapabilityManifest.model_validate(item) for item in items]

    async def register_capability(
        self, manifest: CapabilityManifest
    ) -> CapabilityManifest:
        response = await self._http.post(
            "/capabilities",
            json=manifest.model_dump(exclude_none=True),
            headers=await self._headers(),
        )
        _raise_for_problem_json(response)
        return CapabilityManifest.model_validate(response.json())

    async def get_capability(self, capability_id: str) -> CapabilityManifest:
        response = await self._http.get(
            f"/capabilities/{capability_id}", headers=await self._headers()
        )
        _raise_for_problem_json(response)
        return CapabilityManifest.model_validate(response.json())

    async def submit_task(self, task_request: TaskRequest) -> Task:
        response = await self._http.post(
            "/tasks",
            json=task_request.model_dump(exclude_none=True),
            headers=await self._headers(),
        )
        _raise_for_problem_json(response)
        return Task.model_validate(response.json())

    async def get_task(self, task_id: str) -> Task:
        response = await self._http.get(
            f"/tasks/{task_id}", headers=await self._headers()
        )
        _raise_for_problem_json(response)
        return Task.model_validate(response.json())

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "AsyncHubveryClient":
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self.aclose()
