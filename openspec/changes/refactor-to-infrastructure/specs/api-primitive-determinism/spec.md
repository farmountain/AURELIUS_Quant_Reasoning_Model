## ADDED Requirements

### Requirement: Determinism Scoring API Endpoint
The system SHALL provide a standalone REST API endpoint at `/api/primitives/v1/determinism/score` that accepts backtest results and returns a determinism score indicating result consistency across multiple runs.

#### Scenario: Score single backtest determinism
- **WHEN** client POSTs backtest results with metrics (returns, drawdowns, trade counts) to `/api/primitives/v1/determinism/score`
- **THEN** system returns determinism score (0-100), confidence interval, and pass/fail status based on configurable threshold

#### Scenario: Score with multiple run comparison
- **WHEN** client POSTs array of N backtest runs with identical parameters but different execution timestamps
- **THEN** system calculates variance across runs and returns determinism score with statistical significance (p-value)

#### Scenario: Invalid input rejection
- **WHEN** client POSTs malformed data (missing required fields, negative values, inconsistent timestamps)
- **THEN** system returns HTTP 400 with validation error details in canonical error schema

### Requirement: OpenAPI Specification Contract
The determinism primitive SHALL be fully documented with an OpenAPI 3.0 specification defining request/response schemas, authentication requirements, and error codes.

#### Scenario: OpenAPI spec generation
- **WHEN** developer accesses `/api/primitives/v1/openapi.json`
- **THEN** system returns complete OpenAPI document including determinism endpoint with example requests and responses

#### Scenario: SDK code generation compatibility
- **WHEN** openapi-generator tool processes the OpenAPI specification
- **THEN** generated SDK code compiles without errors and includes type-safe client methods for determinism scoring

### Requirement: Authentication and Authorization
The determinism API SHALL support both API key and JWT token authentication with rate limiting per client.

#### Scenario: API key authentication
- **WHEN** client includes valid API key in `X-API-Key` header
- **THEN** system authenticates request and applies per-key rate limits (1000 requests/hour default)

#### Scenario: JWT token authentication
- **WHEN** client includes valid JWT token in `Authorization: Bearer` header
- **THEN** system authenticates request and applies per-user rate limits (5000 requests/hour)

#### Scenario: Unauthenticated request rejection
- **WHEN** client sends request without valid credentials
- **THEN** system returns HTTP 401 with error message indicating authentication failure

### Requirement: Performance and Scalability
The determinism API SHALL respond within 200ms for p95 latency and support 100 concurrent requests per instance.

#### Scenario: Fast response time
- **WHEN** client submits valid determinism scoring request
- **THEN** system returns result within 200ms (p95 latency) under normal load

#### Scenario: Concurrent request handling
- **WHEN** 100 concurrent clients submit determinism requests
- **THEN** system processes all requests without errors or timeout failures

### Requirement: Backward Compatibility with Legacy Workflow
The determinism primitive SHALL coexist with legacy workflow endpoints during 12-month migration period without conflicts.

#### Scenario: Dual endpoint operation
- **WHEN** legacy endpoint `/api/v1/strategies/{id}/validate` calls determinism logic
- **THEN** system uses same determinism service as primitive API to ensure consistent scoring

#### Scenario: Feature flag isolation
- **WHEN** primitive API disabled via feature flag
- **THEN** system continues serving legacy endpoints without disruption
