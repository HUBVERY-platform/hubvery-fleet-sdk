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
