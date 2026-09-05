# hubvery-sdk

Official Python SDK for the HUBVERY Fleet API.

Built against `spec/openapi.yaml` and the JSON Schema files in
`spec/schemas/`. See the repository root `docs/architecture.md` for
the integration boundary this SDK operates within.

## Status

Pre-1.0, under active development.

## Integration tests

`tests/integration/` runs the SDK against a real, locally started
instance of `sandbox/mock-orchestrator`, rather than mocked HTTP calls.
These require Node.js and that package's dependencies installed
(`npm install` in `sandbox/mock-orchestrator`); they are skipped
automatically if Node is unavailable.
