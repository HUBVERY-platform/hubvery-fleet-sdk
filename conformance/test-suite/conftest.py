"""Fixtures for the conformance suite.

This suite validates a running server's HTTP responses against the real
schemas in spec/schemas, independent of any particular SDK. It is meant
to be run by a partner against their own implementation of the HUBVERY
Fleet API, not just against HUBVERY's own sandbox, so a passing run here
does not depend on HUBVERY's SDKs at all: only httpx and jsonschema.

Point it at any server with:

    BASE_URL=http://localhost:4000 pytest

Defaults to the local sandbox on port 4000 if BASE_URL is not set.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import httpx
import pytest
from jsonschema.validators import Draft202012Validator
from referencing import Registry, Resource

SPEC_SCHEMAS_DIR = Path(__file__).resolve().parent / "spec" / "schemas"
BASE_URL = os.environ.get("BASE_URL", "http://localhost:4000")

SCHEMA_FILES = [
    "capability-manifest.schema.json",
    "task-request.schema.json",
    "task-result.schema.json",
    "error.schema.json",
]


def _load_raw(name: str) -> dict:
    return json.loads((SPEC_SCHEMAS_DIR / name).read_text())


# task-result.schema.json references error.schema.json by relative
# filename ($ref: "error.schema.json"), not by its absolute $id. Without
# a registry telling the validator where "error.schema.json" resolves
# to, it falls back to treating the $ref as relative to the schema's
# $id (an https://schemas.hubvery.com/... URL that does not serve these
# files), and validation fails trying to fetch it over the network.
# Registering every schema under both its $id and its bare filename
# makes both forms of $ref resolve locally, with no network access
# required. This mirrors what a partner integrating in any language
# will need to do to use these schema files together.
_registry = Registry().with_resources(
    (schema["$id"], Resource.from_contents(schema))
    for schema in (_load_raw(name) for name in SCHEMA_FILES)
)
_registry = _registry.with_resources(
    (name, Resource.from_contents(_load_raw(name))) for name in SCHEMA_FILES
)


def load_schema(name: str) -> Draft202012Validator:
    """Return a validator for the named schema with $ref resolution
    against the other schema files in spec/schemas already wired up.
    """
    return Draft202012Validator(_load_raw(name), registry=_registry)


@pytest.fixture(scope="session")
def base_url() -> str:
    try:
        httpx.get(f"{BASE_URL}/health", timeout=2.0)
    except httpx.TransportError as exc:
        pytest.fail(
            f"Could not reach {BASE_URL}/health: {exc}. "
            "Start the server you want to check conformance for, or set "
            "BASE_URL to point at it."
        )
    return BASE_URL


@pytest.fixture(autouse=True)
def _reset_state(base_url):
    # Best-effort reset for implementations that support it (the sandbox
    # does). A real HUBVERY-compatible server under test is not required
    # to implement this; conformance tests should not depend on it for
    # correctness, only for convenience during local development.
    try:
        httpx.post(f"{base_url}/__test__/reset", timeout=1.0)
    except httpx.TransportError:
        pass
