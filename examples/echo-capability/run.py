"""Minimal example of a partner integration using the Python SDK.

Registers a trivial "echo" capability with a running HUBVERY-compatible
server, submits a task to it, and polls until the task reaches a
terminal state. Demonstrates the complete lifecycle described in
docs/architecture.md, with no orchestration logic on either side: this
capability does no real work, and the sandbox does no real routing.

Run against the local sandbox:

    cd sandbox/mock-orchestrator && npm install && npm start &
    cd examples/echo-capability
    pip install -r requirements.txt
    python run.py
"""

from __future__ import annotations

import os
import sys
import time

from hubvery_sdk import CapabilityManifest, HubveryClient, Modality, TaskRequest, TaskStatus

BASE_URL = os.environ.get("HUBVERY_BASE_URL", "http://localhost:4000")
TOKEN_URL = os.environ.get("HUBVERY_TOKEN_URL", f"{BASE_URL}/oauth/token")

ECHO_MANIFEST = CapabilityManifest(
    capability_id="echo-tool",
    name="Echo Tool",
    description="Returns whatever message it is given. Exists to demonstrate the integration lifecycle, not to do real work.",
    version="0.1.0",
    modality=Modality.TEXT,
    input_schema={
        "type": "object",
        "required": ["message"],
        "properties": {"message": {"type": "string"}},
    },
    output_schema={"type": "object"},
)


def main() -> int:
    client = HubveryClient(
        client_id=os.environ.get("HUBVERY_CLIENT_ID", "example-client"),
        client_secret=os.environ.get("HUBVERY_CLIENT_SECRET", "example-secret"),
        base_url=BASE_URL,
        token_url=TOKEN_URL,
    )

    print(f"Registering capability against {BASE_URL} ...")
    try:
        manifest = client.register_capability(ECHO_MANIFEST)
    except Exception as exc:  # noqa: BLE001 - example code, print and exit
        # A 409 here just means a previous run already registered it;
        # that is expected if you run this example more than once
        # against the same sandbox instance.
        print(f"Registration skipped or failed ({exc}); continuing.")
        manifest = ECHO_MANIFEST
    print(f"Registered: {manifest.capability_id} v{manifest.version}")

    print("Submitting a task ...")
    task = client.submit_task(
        TaskRequest(capability_id="echo-tool", input={"message": "hello from the example"})
    )
    print(f"Task {task.task_id} submitted, status: {task.status.value}")

    deadline = time.time() + 5
    while task.status not in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
        if time.time() > deadline:
            print("Task did not reach a terminal state in time.", file=sys.stderr)
            return 1
        time.sleep(0.1)
        task = client.get_task(task.task_id)

    print(f"Final status: {task.status.value}")
    print(f"Result: {task.result}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
