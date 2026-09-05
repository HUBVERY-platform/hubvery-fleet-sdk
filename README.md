# hubvery-fleet-sdk

Official SDK, API specification, and conformance tests for connecting
external agents, services, and tools to the HUBVERY orchestration platform.

## Status

This repository is under active development. The API specification and
SDKs are pre-1.0 and may change before the first stable release.

## What this repository is

- The public integration contract, meaning an API specification, schemas,
  and event definitions, for registering a capability with HUBVERY and
  exchanging tasks, status, and results.
- Reference SDKs for implementing that contract.
- A conformance test suite for validating a partner integration.
- A local sandbox for developing against without a live HUBVERY environment.

## What this repository is not

This repository does not contain HUBVERY's orchestration engine. Routing,
capability selection, planning, and pricing logic are proprietary and are
not part of the public integration surface.

## Getting started

Documentation is in progress. See docs/getting-started.md once published.

## License

Apache License 2.0. See LICENSE.
