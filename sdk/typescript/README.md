# @hubvery/fleet-sdk

Official TypeScript SDK for the HUBVERY Fleet API.

## Installation

```bash
npm install @hubvery/fleet-sdk
```

## Usage

```typescript
import { HubveryClient } from "@hubvery/fleet-sdk";

const client = new HubveryClient({
  clientId: process.env.HUBVERY_CLIENT_ID!,
  clientSecret: process.env.HUBVERY_CLIENT_SECRET!,
});

const task = await client.submitTask({
  capability_id: "your-capability-id",
  input: { message: "hello" },
});
```

## Development

```bash
npm install
npm run build
npm test
```

`npm test` runs the integration suite (`tests/integration.test.ts`)
against a real, locally started instance of
`sandbox/mock-orchestrator`, not mocked HTTP calls. That package's own
dependencies must be installed first (`npm install` in
`sandbox/mock-orchestrator`).

## Design notes

Mirrors the Python SDK's structure: an explicit `TokenManager` handling
OAuth2 client credentials with a 30 second expiry buffer, and a thin
`HubveryClient` covering the six operations in `spec/openapi.yaml`.
Types in `src/models.ts` are kept in sync with `spec/schemas/`.
