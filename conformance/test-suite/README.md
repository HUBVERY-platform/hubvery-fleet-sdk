# HUBVERY Fleet API conformance suite

Validates that a running server correctly implements the HUBVERY Fleet
API v0 contract defined in `spec/openapi.yaml` and `spec/schemas/`. This
suite is independent of any HUBVERY SDK: it uses plain `httpx` and the
actual schema files, so it can validate an implementation written in
any language.

## Running against the local sandbox

```bash
cd sandbox/mock-orchestrator && npm install && npm start &
cd conformance/test-suite
pip install -r requirements.txt
pytest -v
```

## Running against your own implementation

```bash
BASE_URL=https://your-server.example.com pytest -v
```

If your server supports a `POST /__test__/reset` endpoint for clearing
state between test runs, the suite will use it automatically. This is
not part of the public API contract and is not required for a passing
run; its absence is handled gracefully.

## What this suite checks

- Response shapes conform to `spec/schemas/*.schema.json`, including
  correct `$ref` resolution between schema files (for example,
  `task-result.schema.json`'s reference to `error.schema.json`).
- Documented status codes for both success and error cases: `201`,
  `202`, `400`, `404`, `409`.
- Errors conform to the RFC 7807 `error.schema.json` shape.
- A submitted task reaches one of the documented terminal states
  (`completed`, `failed`, `cancelled`) within a bounded time.

This suite intentionally does not check routing, scoring, pricing, or
any other proprietary orchestration behavior, since none of that is
part of the public contract.
