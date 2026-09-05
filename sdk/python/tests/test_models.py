from hubvery_sdk.models import CapabilityManifest, Modality, Task, TaskStatus


def test_capability_manifest_minimal():
    manifest = CapabilityManifest(
        capability_id="echo-tool",
        name="Echo Tool",
        version="0.1.0",
        modality=Modality.TEXT,
        input_schema={"type": "object"},
        output_schema={"type": "object"},
    )
    assert manifest.capability_id == "echo-tool"
    assert manifest.constraints is None


def test_task_requires_input_status():
    task = Task(
        task_id="task_123",
        capability_id="echo-tool",
        status=TaskStatus.REQUIRES_INPUT,
        created_at="2026-01-01T00:00:00Z",
        updated_at="2026-01-01T00:05:00Z",
    )
    assert task.status == TaskStatus.REQUIRES_INPUT
    assert task.result is None
