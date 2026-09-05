"""Conformance tests for the HUBVERY Fleet API v0 contract.

Each test validates the server's actual response bytes against the real
schema files in spec/schemas, using jsonschema directly rather than any
HUBVERY-authored SDK model. A server that passes this suite conforms to
the public contract, regardless of what language or framework it is
implemented in.
"""

from __future__ import annotations

import time

import httpx

from conftest import load_schema

CAPABILITY_MANIFEST_SCHEMA = load_schema("capability-manifest.schema.json")
TASK_RESULT_SCHEMA = load_schema("task-result.schema.json")
ERROR_SCHEMA = load_schema("error.schema.json")


def validate_schema(instance, schema):
    schema.validate(instance)


ECHO_MANIFEST = {
    "capability_id": "echo-tool",
    "name": "Echo Tool",
    "version": "0.1.0",
    "modality": "text",
    "input_schema": {
        "type": "object",
        "required": ["message"],
        "properties": {"message": {"type": "string"}},
    },
    "output_schema": {"type": "object"},
}


def test_health_endpoint_returns_ok(base_url):
    response = httpx.get(f"{base_url}/health")
    assert response.status_code == 200
    body = response.json()
    assert body.get("status") == "ok"


def test_capability_registration_conforms_to_schema(base_url):
    response = httpx.post(f"{base_url}/capabilities", json=ECHO_MANIFEST)
    assert response.status_code == 201
    validate_schema(instance=response.json(), schema=CAPABILITY_MANIFEST_SCHEMA)


def test_invalid_capability_manifest_returns_conformant_error(base_url):
    response = httpx.post(f"{base_url}/capabilities", json={"name": "incomplete"})
    assert response.status_code == 400
    validate_schema(instance=response.json(), schema=ERROR_SCHEMA)


def test_duplicate_capability_registration_returns_409(base_url):
    httpx.post(f"{base_url}/capabilities", json=ECHO_MANIFEST)
    response = httpx.post(f"{base_url}/capabilities", json=ECHO_MANIFEST)
    assert response.status_code == 409
    validate_schema(instance=response.json(), schema=ERROR_SCHEMA)


def test_get_unknown_capability_returns_conformant_404(base_url):
    response = httpx.get(f"{base_url}/capabilities/does-not-exist")
    assert response.status_code == 404
    validate_schema(instance=response.json(), schema=ERROR_SCHEMA)


def test_task_submission_conforms_to_schema(base_url):
    httpx.post(f"{base_url}/capabilities", json=ECHO_MANIFEST)
    response = httpx.post(
        f"{base_url}/tasks",
        json={"capability_id": "echo-tool", "input": {"message": "hello"}},
    )
    assert response.status_code == 202
    body = response.json()
    validate_schema(instance=body, schema=TASK_RESULT_SCHEMA)
    assert body["status"] in ("queued", "running")


def test_task_input_validation_returns_conformant_error(base_url):
    httpx.post(f"{base_url}/capabilities", json=ECHO_MANIFEST)
    response = httpx.post(
        f"{base_url}/tasks",
        json={"capability_id": "echo-tool", "input": {"wrong_field": 1}},
    )
    assert response.status_code == 400
    validate_schema(instance=response.json(), schema=ERROR_SCHEMA)


def test_task_for_unknown_capability_returns_conformant_404(base_url):
    response = httpx.post(
        f"{base_url}/tasks", json={"capability_id": "does-not-exist", "input": {}}
    )
    assert response.status_code == 404
    validate_schema(instance=response.json(), schema=ERROR_SCHEMA)


def test_task_reaches_a_terminal_state(base_url):
    httpx.post(f"{base_url}/capabilities", json=ECHO_MANIFEST)
    submitted = httpx.post(
        f"{base_url}/tasks",
        json={"capability_id": "echo-tool", "input": {"message": "hello"}},
    ).json()

    terminal_states = {"completed", "failed", "cancelled"}
    deadline = time.time() + 5
    status = submitted["status"]
    task_id = submitted["task_id"]

    while status not in terminal_states:
        if time.time() > deadline:
            raise AssertionError(
                f"Task did not reach a terminal state within 5s; last status: {status}"
            )
        time.sleep(0.1)
        polled = httpx.get(f"{base_url}/tasks/{task_id}")
        validate_schema(instance=polled.json(), schema=TASK_RESULT_SCHEMA)
        status = polled.json()["status"]


def test_get_unknown_task_returns_conformant_404(base_url):
    response = httpx.get(f"{base_url}/tasks/nonexistent")
    assert response.status_code == 404
    validate_schema(instance=response.json(), schema=ERROR_SCHEMA)
