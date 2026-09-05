# hubvery-fleet-sdk mock orchestrator

A local sandbox implementing the HUBVERY Fleet API v0 (`spec/openapi.yaml`)
for development against, without a live HUBVERY environment.

This is a mock, not a reference implementation of orchestration. It
validates requests against the real JSON Schemas in `spec/schemas` and
simulates task completion with a canned result (`{ "echo": <input> }`).
It performs no routing, scoring, or planning, and should not be used as
a model for how the production orchestration engine behaves.

## Running

```bash
npm install
npm start
```

The server listens on `http://localhost:4000` by default, matching the
sandbox entry in `spec/openapi.yaml`'s `servers` block. Set `PORT` to
use a different port.

## Testing

```bash
npm test
```

Runs the automated test suite (`src/server.test.js`) using Node's
built-in test runner against a real instance of the server, not a mock
of it.

## Endpoints implemented

- `GET /health`
- `POST /oauth/token` (mock; accepts any non-empty client_id and
  client_secret, not part of the public API surface, exists so the
  sandbox is usable end to end without a real auth provider)
- `GET /capabilities`
- `POST /capabilities`
- `GET /capabilities/:capability_id`
- `POST /tasks`
- `GET /tasks/:task_id`
- `POST /__test__/reset` (test-only, clears in-memory state; not part of
  the public API surface)
