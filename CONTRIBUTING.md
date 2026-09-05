# Contributing to hubvery-fleet-sdk

Thank you for considering a contribution. This repository defines the public
integration contract, reference SDKs, and conformance tests that external
partners use to connect capabilities to the HUBVERY orchestration platform.

## Before you start

Check open issues before starting new work, to avoid duplicate effort.
Changes to `spec/` (the API specification, JSON Schemas, and event
definitions) require a maintainer review and, for breaking changes, an
associated RFC issue describing the motivation and migration path.
All SDK changes must pass the conformance test suite in `conformance/`.

## Development setup

Setup instructions for each SDK language live in that language's directory
under `sdk/`.

## Pull requests

Keep PRs scoped to a single logical change. Include tests for new behavior.
Update relevant documentation in `docs/` alongside code changes.

## Reporting bugs

Open a GitHub issue using the provided templates. Include reproduction steps
and the SDK language and version affected.
