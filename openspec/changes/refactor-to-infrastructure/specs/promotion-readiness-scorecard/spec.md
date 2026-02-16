## MODIFIED Requirements

### Requirement: Promotion readiness SHALL be computed as a weighted scorecard
The system SHALL compute a promotion readiness score `S` as a weighted combination of normalized components (`D`, `R`, `P`, `O`, `U`) where each component is constrained to `[0,100]` and default weights are explicitly versioned. The scorecard SHALL be exposed as a standalone API primitive at `/api/primitives/v1/readiness/score` with OpenAPI specification.

#### Scenario: Score computed with default weights
- **WHEN** readiness is evaluated without tenant overrides via primitive API
- **THEN** the system computes `S` using the default weight profile and returns component-level contributions in canonical response envelope

#### Scenario: Component normalization fails
- **WHEN** one or more component inputs are missing or out of bounds
- **THEN** the system clamps invalid values, records data-quality warnings, and returns a score with explicit uncertainty flags

#### Scenario: External integration via SDK
- **WHEN** external developer calls `client.readiness.score(strategy_id)` using Python SDK
- **THEN** SDK returns typed ReadinessScore object with score, components, band, and blockers

### Requirement: Hard blockers SHALL override weighted score bands
The system SHALL enforce non-compensatory hard blockers (including `missing_run_identity`, parity failure, and lineage/policy blockers) such that a blocked decision cannot be promoted regardless of weighted score. Hard blocker logic SHALL be consistent across legacy workflow endpoints and new primitive API.

#### Scenario: High score with hard blocker
- **WHEN** weighted score is in Green range but one or more hard blockers are present
- **THEN** final readiness decision is blocked and the response includes blocker rationale and remediation actions

#### Scenario: No hard blockers
- **WHEN** no hard blockers are present
- **THEN** final decision band is derived from configured score thresholds

#### Scenario: Blocker consistency check
- **WHEN** same strategy evaluated via legacy `/api/v1/strategies/{id}/validate` and primitive `/api/primitives/v1/readiness/score`
- **THEN** both endpoints return identical hard blocker status and readiness decision

### Requirement: Readiness output SHALL be operator-actionable
The readiness payload SHALL include decision band, top blocker list, and prioritized next actions for operators. The response format SHALL conform to canonical envelope schema for primitive APIs.

#### Scenario: Operator inspects readiness panel
- **WHEN** API or dashboard renders readiness output
- **THEN** the user sees score, band, top blockers, and concrete next actions in a stable canonical format

#### Scenario: Decision state changes between evaluations
- **WHEN** readiness inputs change between evaluations
- **THEN** the payload includes transition-aware context indicating which components drove the state change

#### Scenario: API response envelope
- **WHEN** external developer calls primitive readiness API
- **THEN** response includes `data` (scorecard), `meta` (version, timestamp), and `links` (related resources) in standardized envelope

## ADDED Requirements

### Requirement: Readiness Primitive API Authentication
The readiness scoring primitive SHALL support both API key and JWT token authentication with per-client rate limiting.

#### Scenario: API key authentication
- **WHEN** external developer includes valid API key in request header
- **THEN** system authenticates and applies 1000 requests/hour rate limit

#### Scenario: JWT token authentication for dashboard
- **WHEN** dashboard client includes valid JWT token
- **THEN** system authenticates and applies 5000 requests/hour rate limit

### Requirement: Readiness Primitive Performance
The readiness scoring API SHALL respond within 200ms (p95 latency) for synchronous score computation.

#### Scenario: Fast score computation
- **WHEN** client submits readiness request with strategy ID
- **THEN** system returns scorecard within 200ms under normal load

#### Scenario: Concurrent request handling
- **WHEN** 100 concurrent clients request readiness scores
- **THEN** system processes all requests without timeout or error
