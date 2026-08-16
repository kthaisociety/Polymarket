# Tests

> General conventions for test organization and behavior.

## Test observable behavior

Test what callers and users can observe. Avoid assertions that merely freeze private implementation
details. A refactor that preserves behavior should not require unrelated tests to change.

## Keep ownership clear

Where practical, mirror the source layout and give each test file one primary subject. Cross-module
flows belong in integration tests named for the behavior being exercised.

The repository's test configuration is the source of truth for filenames, directories, markers, and
collection rules.

## Use the real production path

Drive production functions through their public or intentionally testable seams. Replace external
boundaries such as network clients, clocks, providers, and storage services. Keep internal domain
logic real.

Prefer a small fake that implements a project-owned interface over a mock that asserts a sequence of
private calls.

## Separate test scopes

- **Unit tests** exercise a focused contract without real external infrastructure.
- **Integration tests** verify wiring across real internal components and controlled infrastructure.
- **Contract tests** verify adapters against project-owned interfaces.
- **End-to-end tests** cover a small number of critical user-visible flows.
- **Scientific and adversarial tests** belong to the specification's testing strategy, not this
  code-style guide.

## Make tests reproducible

Control clocks, random seeds, model outputs, and external observations. A test should explain its
failure without relying on execution order or live services.

## Share only genuine plumbing

Put setup shared by several test files in fixtures or support modules. Keep scenario-specific values
near the test because they document the behavior under test.

## Do not weaken production design for tests

Do not make a member public only because a test wants access. Prefer testing through a stable seam.
If direct internal access is deliberately allowed, configure that exception narrowly for test code.
