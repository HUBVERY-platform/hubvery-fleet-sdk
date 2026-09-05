"""Fixtures for integration tests that run against a real, running
instance of sandbox/mock-orchestrator, rather than mocked HTTP calls.

These require Node.js and the mock orchestrator's dependencies to be
installed (npm install in sandbox/mock-orchestrator). If Node is not
available, these tests are skipped rather than failed, since they are
integration tests, not part of the unit test suite that must always run.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import time
from pathlib import Path

import httpx
import pytest

SANDBOX_DIR = Path(__file__).resolve().parents[4] / "sandbox" / "mock-orchestrator"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="session")
def sandbox_server():
    if shutil.which("node") is None:
        pytest.skip("Node.js is not available; skipping integration tests.")
    if not (SANDBOX_DIR / "node_modules").exists():
        pytest.skip(
            f"Dependencies not installed in {SANDBOX_DIR}. Run 'npm install' there first."
        )

    port = _free_port()
    process = subprocess.Popen(
        ["node", "src/server.js"],
        cwd=SANDBOX_DIR,
        env={**os.environ, "PORT": str(port)},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    base_url = f"http://localhost:{port}"
    for _ in range(50):
        try:
            httpx.get(f"{base_url}/health", timeout=0.2)
            break
        except httpx.TransportError:
            time.sleep(0.1)
    else:
        process.terminate()
        raise RuntimeError("sandbox server did not become healthy in time")

    yield base_url

    process.terminate()
    process.wait(timeout=5)


@pytest.fixture(autouse=True)
def _reset_sandbox_state(sandbox_server):
    httpx.post(f"{sandbox_server}/__test__/reset")
