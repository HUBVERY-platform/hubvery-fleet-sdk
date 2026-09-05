"""Integration tests exercising the SDK against a real, running instance
of sandbox/mock-orchestrator over actual HTTP, with nothing mocked.

These complement, and are deliberately separate from, tests/test_client.py,
which uses respx to mock every HTTP call and tests the client's own
logic in isolation. These tests instead catch the class of bug that
mocked tests structurally cannot: mismatches between what the SDK sends
and what a real server expects or returns.
"""

from __future__ import annotations

import time

import pytest

from hubvery_sdk.client import HubveryClient
from hubvery_sdk.exceptions import HubveryAPIError
from hubvery_sdk.models import CapabilityManifest, Modality, TaskRequest, TaskStatus

ECHO_MANIFEST = CapabilityManifest(
    capability_id="echo-tool",
    name="Echo Tool",
    version="0.1.0",
    modality=Modality.TEXT,
    input_schema={
        "type": "object",
        "required": ["message"],
        "properties": {"message": {"type": "string"}},
    },
    output_schema={"type": "object"},
)


def _client(sandbox_server: str) -> HubveryClient:
    return HubveryClient(
        client_id="id",
        client_secret="secret",
        base_url=sandbox_server,
        token_url=f"{sandbox_server}/oauth/token",
    )


def test_get_health_against_real_server(sandbox_server):
    client = _client(sandbox_server)
    assert client.get_health() == {"status": "ok"}


def test_register_and_retrieve_capability(sandbox_server):
    client = _client(sandbox_server)
    registered = client.register_capability(ECHO_MANIFEST)
    assert registered.capability_id == "echo-tool"

    fetched = client.get_capability("echo-tool")
    assert fetched.name == "Echo Tool"


def test_duplicate_registration_raises_409(sandbox_server):
    client = _client(sandbox_server)
    client.register_capability(ECHO_MANIFEST)

    with pytest.raises(HubveryAPIError) as exc_info:
        client.register_capability(ECHO_MANIFEST)

    assert exc_info.value.status == 409


def test_full_task_lifecycle_against_real_server(sandbox_server):
    client = _client(sandbox_server)
    client.register_capability(ECHO_MANIFEST)

    submitted = client.submit_task(
        TaskRequest(capability_id="echo-tool", input={"message": "hello"})
    )
    assert submitted.status == TaskStatus.QUEUED

    deadline = time.time() + 2
    task = submitted
    while task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED):
        if time.time() > deadline:
            pytest.fail(f"task did not complete in time, last status: {task.status}")
        time.sleep(0.05)
        task = client.get_task(submitted.task_id)

    assert task.status == TaskStatus.COMPLETED
    assert task.result == {"echo": {"message": "hello"}}


def test_invalid_task_input_surfaces_real_validation_error(sandbox_server):
    client = _client(sandbox_server)
    client.register_capability(ECHO_MANIFEST)

    with pytest.raises(HubveryAPIError) as exc_info:
        client.submit_task(
            TaskRequest(capability_id="echo-tool", input={"wrong_field": 1})
        )

    assert exc_info.value.status == 400


def test_task_for_unknown_capability_raises_404(sandbox_server):
    client = _client(sandbox_server)

    with pytest.raises(HubveryAPIError) as exc_info:
        client.submit_task(TaskRequest(capability_id="does-not-exist", input={}))

    assert exc_info.value.status == 404
