# Event Types

All asynchronous events HUBVERY emits, whether via webhook or a future
streaming endpoint, are wrapped in the CloudEvents v1.0 envelope. The
`data` field of each event conforms to the schema referenced below.

| Type | Emitted when | `data` schema |
|---|---|---|
| `com.hubvery.task.created` | A task is accepted via `POST /tasks`. | `task-result.schema.json`, status `queued` |
| `com.hubvery.task.started` | A capability begins processing a task. | `task-result.schema.json`, status `running` |
| `com.hubvery.task.requires_input` | A capability pauses a task pending human or partner input. | `task-result.schema.json`, status `requires_input` |
| `com.hubvery.task.completed` | A task finishes successfully. | `task-result.schema.json`, status `completed` |
| `com.hubvery.task.failed` | A task fails. | `task-result.schema.json`, status `failed`, `error` populated |
| `com.hubvery.task.cancelled` | A task is cancelled. | `task-result.schema.json`, status `cancelled` |
| `com.hubvery.capability.registered` | A capability is successfully registered. | `capability-manifest.schema.json` |
| `com.hubvery.capability.updated` | A capability manifest is updated. | `capability-manifest.schema.json` |

## Envelope example

```json
{
  "specversion": "1.0",
  "type": "com.hubvery.task.completed",
  "source": "https://api.hubvery.com/v0",
  "id": "a1b2c3d4",
  "time": "2026-09-04T12:00:00Z",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "task_9f8e7d6c",
    "capability_id": "image-classify-v1",
    "status": "completed"
  }
}
```

## Delivery

Events are delivered to the `callback_url` supplied in the task request,
as an HTTP POST with a CloudEvents JSON envelope in the body. Each request
includes an `X-Hubvery-Signature` header, an HMAC-SHA256 signature of the
raw request body using a per-partner shared secret. Verify this signature
before trusting the payload.
