# Architecture

HUBVERY orchestrates a fleet of independent capabilities, agents, and
services and routes tasks to them based on what each one declares it can
do. This document describes the public integration surface: what a
partner needs to implement to become HUBVERY-compatible, and where that
surface stops.

## Boundary
EXTERNAL PARTNER (agent / service / tool)
       |
       | 1. Capability declaration (JSON Schema manifest)
       | 2. Registration and authentication (OAuth2 client credentials)
       | 3. Task submission (POST /tasks)
       | 4. Task status (GET /tasks/{id})
       | 5. Result and event delivery (webhook, CloudEvents envelope)
       | 6. Error reporting (RFC 7807 problem+json)
       v
+-----------------------------------------------+
|          HUBVERY PUBLIC INTEGRATION LAYER      |
|  This repository documents and implements      |
|  everything in this box.                       |
|                                                 |
|  - Capability registry (spec/openapi.yaml)      |
|  - Auth and identity verification              |
|  - Task submission and status endpoints         |
|  - Event and webhook dispatch                  |
|  - Conformance test harness                    |
|  - Reference SDKs                              |
+-----------------------------------------------+
       |
======= boundary: private beyond this point =====
       |
       v
+-----------------------------------------------+
|          HUBVERY ORCHESTRATION ENGINE          |
|          (not part of this repository)         |
|                                                 |
|  - Capability selection and scoring            |
|  - Routing and planning                        |
|  - Multi-agent task decomposition              |
|  - Pricing and economic logic                  |
|  - Internal state and workflow persistence      |
+-----------------------------------------------+


A partner implementing this repository's specification can register a
capability, receive tasks, and return results without any visibility
into how HUBVERY decides which capability handles a given task, what it
costs, or how a multi-step request is broken down. That decision layer
is proprietary and is intentionally outside the scope of this repository.

## Lifecycle of a task

1. A partner registers a capability by submitting a manifest conforming
   to `spec/schemas/capability-manifest.schema.json` to `POST /capabilities`.
2. A client submits a task to that capability via `POST /tasks`, with a
   payload conforming to `spec/schemas/task-request.schema.json`.
3. HUBVERY validates the input against the capability's declared
   `input_schema` and accepts or rejects the request.
4. The task moves through the states defined in
   `spec/schemas/task-result.schema.json`: `queued`, `running`,
   optionally `requires_input`, then `completed`, `failed`, or
   `cancelled`.
5. State changes are emitted as CloudEvents, delivered to the
   `callback_url` supplied at submission time. See
   `spec/events/cloudevents-types.md` for the full event catalog.
6. The caller can also poll `GET /tasks/{id}` directly instead of, or in
   addition to, relying on webhook delivery.

## Standards this specification builds on

This repository does not define a new orchestration protocol. It
combines existing, established standards:

- **OpenAPI 3.1** for the REST contract (`spec/openapi.yaml`).
- **JSON Schema (2020-12)** for capability manifests, task payloads, and
  results.
- **OAuth 2.0 client credentials** for partner authentication.
- **CloudEvents 1.0** for the event envelope format.
- **RFC 7807 (Problem Details)** for error responses.

Where a partner's capability is itself an agent, the concepts here are
intended to be compatible with the Agent-to-Agent (A2A) protocol's task
lifecycle and capability card vocabulary. Where a capability is
tool-like, it can be exposed through the Model Context Protocol (MCP) as
an alternative ingestion path. Neither is required to integrate with
this specification, and this repository does not currently include a
full A2A or MCP implementation.

## What this repository does not cover

- How HUBVERY selects a capability among several that could handle a
  given task.
- How HUBVERY prices or bills for task execution.
- HUBVERY's internal state management or infrastructure.

These are proprietary to HUBVERY's orchestration engine and are outside
the scope of the public integration contract.

## Versioning

The API is versioned in the URL path (`/v0` for this pre-1.0 release).
Each capability manifest carries its own semantic version, independent
of the API version. Breaking changes to `spec/` require an RFC issue,
per `CONTRIBUTING.md`.
