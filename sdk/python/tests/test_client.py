import httpx
import pytest
import respx

from hubvery_sdk.client import HubveryClient
from hubvery_sdk.exceptions import HubveryAPIError
from hubvery_sdk.models import TaskRequest, TaskStatus

TOKEN_URL = "https://auth.hubvery.com/oauth/token"
BASE_URL = "https://api.hubvery.com/v0"


def _mock_token_response(router: respx.MockRouter) -> None:
    router.post(TOKEN_URL).mock(
        return_value=httpx.Response(
            200,
            json={"access_token": "fake-token-123", "expires_in": 3600},
        )
    )


@respx.mock
def test_submit_task_success():
    _mock_token_response(respx)
    respx.post(f"{BASE_URL}/tasks").mock(
        return_value=httpx.Response(
            202,
            json={
                "task_id": "task_abc",
                "capability_id": "echo-tool",
                "status": "queued",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            },
        )
    )

    client = HubveryClient(client_id="id", client_secret="secret")
    task = client.submit_task(
        TaskRequest(capability_id="echo-tool", input={"message": "hello"})
    )

    assert task.task_id == "task_abc"
    assert task.status == TaskStatus.QUEUED

    # Confirm the Authorization header was actually sent with the token
    # from the mocked token endpoint, not just that a request happened.
    sent_request = respx.calls.last.request
    assert sent_request.headers["Authorization"] == "Bearer fake-token-123"


@respx.mock
def test_get_task_not_found_raises_api_error():
    _mock_token_response(respx)
    respx.get(f"{BASE_URL}/tasks/does-not-exist").mock(
        return_value=httpx.Response(
            404,
            json={
                "type": "https://errors.hubvery.com/task-not-found",
                "title": "Task not found",
                "status": 404,
                "detail": "No task found with this id.",
            },
        )
    )

    client = HubveryClient(client_id="id", client_secret="secret")

    with pytest.raises(HubveryAPIError) as exc_info:
        client.get_task("does-not-exist")

    assert exc_info.value.status == 404
    assert exc_info.value.title == "Task not found"


@respx.mock
def test_token_is_cached_across_requests():
    token_route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(
            200,
            json={"access_token": "fake-token-123", "expires_in": 3600},
        )
    )
    respx.get(f"{BASE_URL}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )
    respx.get(f"{BASE_URL}/capabilities").mock(
        return_value=httpx.Response(200, json={"items": []})
    )

    client = HubveryClient(client_id="id", client_secret="secret")
    client.list_capabilities()
    client.list_capabilities()

    # Two API calls, but the token endpoint should only be hit once,
    # since the token has not expired between calls.
    assert token_route.call_count == 1


@respx.mock
def test_register_capability_success():
    _mock_token_response(respx)
    manifest_payload = {
        "capability_id": "echo-tool",
        "name": "Echo Tool",
        "version": "0.1.0",
        "modality": "text",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
    }
    respx.post(f"{BASE_URL}/capabilities").mock(
        return_value=httpx.Response(201, json=manifest_payload)
    )

    from hubvery_sdk.models import CapabilityManifest, Modality

    client = HubveryClient(client_id="id", client_secret="secret")
    manifest = client.register_capability(
        CapabilityManifest(
            capability_id="echo-tool",
            name="Echo Tool",
            version="0.1.0",
            modality=Modality.TEXT,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
        )
    )

    assert manifest.capability_id == "echo-tool"
    assert manifest.modality == Modality.TEXT


@respx.mock
def test_get_capability_success():
    _mock_token_response(respx)
    respx.get(f"{BASE_URL}/capabilities/echo-tool").mock(
        return_value=httpx.Response(
            200,
            json={
                "capability_id": "echo-tool",
                "name": "Echo Tool",
                "version": "0.1.0",
                "modality": "text",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            },
        )
    )

    client = HubveryClient(client_id="id", client_secret="secret")
    manifest = client.get_capability("echo-tool")

    assert manifest.capability_id == "echo-tool"
    assert manifest.name == "Echo Tool"


@respx.mock
def test_error_response_without_valid_problem_json_still_raises():
    # Simulates an upstream proxy or unexpected server error that returns
    # a 500 with a body that does NOT conform to error.schema.json (e.g.
    # a plain-text or malformed error page). The client should not crash
    # trying to parse it as an Error model; it should fall back to
    # httpx's own raise_for_status behavior.
    _mock_token_response(respx)
    respx.get(f"{BASE_URL}/tasks/broken").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    client = HubveryClient(client_id="id", client_secret="secret")

    with pytest.raises(httpx.HTTPStatusError):
        client.get_task("broken")


from hubvery_sdk.client import AsyncHubveryClient


@respx.mock
@pytest.mark.asyncio
async def test_async_submit_task_success():
    _mock_token_response(respx)
    respx.post(f"{BASE_URL}/tasks").mock(
        return_value=httpx.Response(
            202,
            json={
                "task_id": "task_abc",
                "capability_id": "echo-tool",
                "status": "queued",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            },
        )
    )

    client = AsyncHubveryClient(client_id="id", client_secret="secret")
    task = await client.submit_task(
        TaskRequest(capability_id="echo-tool", input={"message": "hello"})
    )
    await client.aclose()

    assert task.task_id == "task_abc"
    assert task.status == TaskStatus.QUEUED


@respx.mock
@pytest.mark.asyncio
async def test_async_get_task_not_found_raises_api_error():
    _mock_token_response(respx)
    respx.get(f"{BASE_URL}/tasks/does-not-exist").mock(
        return_value=httpx.Response(
            404,
            json={
                "type": "https://errors.hubvery.com/task-not-found",
                "title": "Task not found",
                "status": 404,
                "detail": "No task found with this id.",
            },
        )
    )

    client = AsyncHubveryClient(client_id="id", client_secret="secret")

    with pytest.raises(HubveryAPIError) as exc_info:
        await client.get_task("does-not-exist")
    await client.aclose()

    assert exc_info.value.status == 404
    assert exc_info.value.title == "Task not found"


@respx.mock
@pytest.mark.asyncio
async def test_async_token_is_cached_across_requests():
    token_route = respx.post(TOKEN_URL).mock(
        return_value=httpx.Response(
            200,
            json={"access_token": "fake-token-123", "expires_in": 3600},
        )
    )
    respx.get(f"{BASE_URL}/capabilities").mock(
        return_value=httpx.Response(200, json={"items": []})
    )

    client = AsyncHubveryClient(client_id="id", client_secret="secret")
    await client.list_capabilities()
    await client.list_capabilities()
    await client.aclose()

    assert token_route.call_count == 1


@respx.mock
@pytest.mark.asyncio
async def test_async_context_manager_closes_client():
    _mock_token_response(respx)
    respx.get(f"{BASE_URL}/capabilities").mock(
        return_value=httpx.Response(200, json={"items": []})
    )

    async with AsyncHubveryClient(client_id="id", client_secret="secret") as client:
        result = await client.list_capabilities()
        assert result == []


@respx.mock
def test_get_health():
    respx.get(f"{BASE_URL}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )

    client = HubveryClient(client_id="id", client_secret="secret")
    health = client.get_health()

    assert health == {"status": "ok"}


@respx.mock
def test_submit_task_with_optional_fields():
    _mock_token_response(respx)
    respx.post(f"{BASE_URL}/tasks").mock(
        return_value=httpx.Response(
            202,
            json={
                "task_id": "task_xyz",
                "capability_id": "echo-tool",
                "status": "queued",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            },
        )
    )

    client = HubveryClient(client_id="id", client_secret="secret")
    client.submit_task(
        TaskRequest(
            capability_id="echo-tool",
            input={"message": "hello"},
            callback_url="https://partner.example.com/webhooks",
            idempotency_key="request-42",
        )
    )

    sent_body = respx.calls.last.request.content
    import json

    payload = json.loads(sent_body)
    assert payload["callback_url"] == "https://partner.example.com/webhooks"
    assert payload["idempotency_key"] == "request-42"


@respx.mock
def test_sync_close_and_context_manager():
    with HubveryClient(client_id="id", client_secret="secret") as client:
        assert client._http.is_closed is False
    assert client._http.is_closed is True


@respx.mock
@pytest.mark.asyncio
async def test_async_get_health():
    respx.get(f"{BASE_URL}/health").mock(
        return_value=httpx.Response(200, json={"status": "ok"})
    )

    client = AsyncHubveryClient(client_id="id", client_secret="secret")
    health = await client.get_health()
    await client.aclose()

    assert health == {"status": "ok"}


@respx.mock
@pytest.mark.asyncio
async def test_async_register_capability_success():
    from hubvery_sdk.models import CapabilityManifest, Modality

    _mock_token_response(respx)
    manifest_payload = {
        "capability_id": "echo-tool",
        "name": "Echo Tool",
        "version": "0.1.0",
        "modality": "text",
        "input_schema": {"type": "object"},
        "output_schema": {"type": "object"},
    }
    respx.post(f"{BASE_URL}/capabilities").mock(
        return_value=httpx.Response(201, json=manifest_payload)
    )

    client = AsyncHubveryClient(client_id="id", client_secret="secret")
    manifest = await client.register_capability(
        CapabilityManifest(
            capability_id="echo-tool",
            name="Echo Tool",
            version="0.1.0",
            modality=Modality.TEXT,
            input_schema={"type": "object"},
            output_schema={"type": "object"},
        )
    )
    await client.aclose()

    assert manifest.capability_id == "echo-tool"
    assert manifest.modality == Modality.TEXT


@respx.mock
@pytest.mark.asyncio
async def test_async_get_capability_success():
    _mock_token_response(respx)
    respx.get(f"{BASE_URL}/capabilities/echo-tool").mock(
        return_value=httpx.Response(
            200,
            json={
                "capability_id": "echo-tool",
                "name": "Echo Tool",
                "version": "0.1.0",
                "modality": "text",
                "input_schema": {"type": "object"},
                "output_schema": {"type": "object"},
            },
        )
    )

    client = AsyncHubveryClient(client_id="id", client_secret="secret")
    manifest = await client.get_capability("echo-tool")
    await client.aclose()

    assert manifest.capability_id == "echo-tool"
    assert manifest.name == "Echo Tool"


@respx.mock
def test_get_task_success():
    _mock_token_response(respx)
    respx.get(f"{BASE_URL}/tasks/task_abc").mock(
        return_value=httpx.Response(
            200,
            json={
                "task_id": "task_abc",
                "capability_id": "echo-tool",
                "status": "completed",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:05:00Z",
                "result": {"output": "hello"},
            },
        )
    )

    client = HubveryClient(client_id="id", client_secret="secret")
    task = client.get_task("task_abc")

    assert task.task_id == "task_abc"
    assert task.status == TaskStatus.COMPLETED
    assert task.result == {"output": "hello"}


@respx.mock
@pytest.mark.asyncio
async def test_async_get_task_success():
    _mock_token_response(respx)
    respx.get(f"{BASE_URL}/tasks/task_abc").mock(
        return_value=httpx.Response(
            200,
            json={
                "task_id": "task_abc",
                "capability_id": "echo-tool",
                "status": "completed",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:05:00Z",
                "result": {"output": "hello"},
            },
        )
    )

    client = AsyncHubveryClient(client_id="id", client_secret="secret")
    task = await client.get_task("task_abc")
    await client.aclose()

    assert task.task_id == "task_abc"
    assert task.status == TaskStatus.COMPLETED
    assert task.result == {"output": "hello"}


def test_token_request_failure_raises_auth_error():
    import respx as respx_module
    from hubvery_sdk.auth import TokenManager
    from hubvery_sdk.exceptions import HubveryAuthError

    with respx_module.mock:
        respx_module.post(TOKEN_URL).mock(
            return_value=httpx.Response(401, text="invalid client credentials")
        )
        manager = TokenManager("bad-id", "bad-secret", scopes=["tasks:read"])
        with httpx.Client() as http:
            with pytest.raises(HubveryAuthError, match="Token request failed"):
                manager.get_token_sync(http)


def test_token_response_missing_access_token_raises_auth_error():
    import respx as respx_module
    from hubvery_sdk.auth import TokenManager
    from hubvery_sdk.exceptions import HubveryAuthError

    with respx_module.mock:
        respx_module.post(TOKEN_URL).mock(
            return_value=httpx.Response(200, json={"token_type": "bearer"})
        )
        manager = TokenManager("id", "secret", scopes=["tasks:read"])
        with httpx.Client() as http:
            with pytest.raises(HubveryAuthError, match="missing 'access_token'"):
                manager.get_token_sync(http)
