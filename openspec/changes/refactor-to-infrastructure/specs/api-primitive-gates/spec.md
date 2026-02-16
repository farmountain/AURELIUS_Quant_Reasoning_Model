## ADDED Requirements

### Requirement: Gate Verification Primitive API
The system SHALL provide a standalone REST API endpoint at `/api/primitives/v1/gates/verify` that accepts strategy metadata and returns gate verification results with promotion readiness assessment.

#### Scenario: Verify strategy against production gate
- **WHEN** client POSTs strategy ID and target environment to `/api/primitives/v1/gates/verify`
- **THEN** system evaluates all gate checks (determinism, risk, policy, evidence) and returns pass/fail with detailed breakdown

#### Scenario: Custom gate configuration
- **WHEN** client includes custom gate definition with configurable thresholds in request payload
- **THEN** system evaluates strategy against custom gate rules and returns verification result

#### Scenario: Async verification with webhook
- **WHEN** client POSTs verification request with webhook URL for long-running checks
- **THEN** system returns HTTP 202 with task ID and delivers result to webhook when complete

### Requirement: Promotion Readiness Scorecard Integration
The gate verification primitive SHALL include promotion readiness scorecard (D-R-P-O-U) in response payload with decision band and actionable recommendations.

#### Scenario: Readiness scorecard in gate response
- **WHEN** client requests gate verification for strategy
- **THEN** system includes readiness payload with weighted score, component breakdown, decision band (GREEN/AMBER/RED), and hard blocker status

#### Scenario: Actionable recommendations
- **WHEN** gate verification fails with AMBER or RED decision band
- **THEN** system provides specific improvement actions ranked by impact (e.g., "Add 3 more acceptance tests for determinism coverage")

### Requirement: Composable Gate Definitions
The gate primitive SHALL allow external developers to define custom gates with arbitrary check combinations and thresholds.

#### Scenario: Define custom gate via API
- **WHEN** developer POSTs custom gate definition with check IDs and passing criteria to `/api/primitives/v1/gates/definitions`
- **THEN** system stores gate definition and returns unique gate ID for future verification requests

#### Scenario: Reuse custom gate for multiple strategies
- **WHEN** developer verifies multiple strategies against same custom gate ID
- **THEN** system applies identical gate rules consistently across all verifications

### Requirement: Gate Certification Registry
The system SHALL maintain a public certification registry of strategies that have passed standard production gates with verification timestamps and scores.

#### Scenario: Query certification status
- **WHEN** client GETs `/api/primitives/v1/gates/certifications?strategy_id=<id>`
- **THEN** system returns certification history including timestamps, gate versions, scores, and pass/fail status

#### Scenario: Public certification badge
- **WHEN** strategy passes production gate and developer opts in to public registry
- **THEN** system issues certification badge with unique URL for embedding in documentation

### Requirement: OpenAPI Specification and SDK Support
The gate primitive SHALL be fully specified in OpenAPI format with SDK methods for synchronous and asynchronous verification patterns.

#### Scenario: Synchronous SDK verification
- **WHEN** developer calls `client.gates.verify(strategy_id, gate_id)` in Python SDK
- **THEN** SDK makes synchronous API call and returns typed GateResult object with pass/fail status

#### Scenario: Async webhook pattern
- **WHEN** developer calls `client.gates.verify_async(strategy_id, gate_id, webhook_url)` 
- **THEN** SDK returns task ID immediately and webhook receives GateResult when verification completes
