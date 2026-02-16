## ADDED Requirements

### Requirement: Official Python SDK Package
The system SHALL provide an official Python SDK published to PyPI as `aurelius-financial-reasoning` with type hints, async support, and testing utilities.

#### Scenario: Install SDK via pip
- **WHEN** developer runs `pip install aurelius-financial-reasoning`
- **THEN** SDK installs with dependencies (httpx, pydantic) and exposes `aurelius` module

#### Scenario: Import and initialize client
- **WHEN** developer imports SDK with `from aurelius import Client` and initializes with API key
- **THEN** client object provides methods for all 8 primitives (determinism, risk, policy, strategy, evidence, gates, reflexion, orchestrator)

### Requirement: Type-Safe API Methods
The SDK SHALL provide fully type-hinted methods with Pydantic models for request/response validation and IDE autocomplete support.

#### Scenario: Type hints for determinism scoring
- **WHEN** developer calls `client.determinism.score(backtest_results)`
- **THEN** IDE provides autocomplete for BacktestResults model fields and returns typed DeterminismScore object

#### Scenario: Request validation with Pydantic
- **WHEN** developer passes invalid data (e.g., negative score) to SDK method
- **THEN** Pydantic validation raises ValueError with detailed error message before API call

### Requirement: Automatic Retry and Exponential Backoff
The SDK SHALL automatically retry failed requests with exponential backoff (3 attempts, max 10 seconds) for transient errors (5xx, timeouts).

#### Scenario: Retry on 503 service unavailable
- **WHEN** API returns HTTP 503 on first request
- **THEN** SDK retries after 1 second, then 2 seconds, then 4 seconds before raising exception

#### Scenario: No retry on client errors
- **WHEN** API returns HTTP 400 bad request
- **THEN** SDK immediately raises validation error without retry attempts

### Requirement: Local Testing Harness with Mock Responses
The SDK SHALL include testing utilities for mocking API responses to enable local development without live API calls.

#### Scenario: Mock client for unit tests
- **WHEN** developer creates `MockClient()` in test suite
- **THEN** mock client returns predefined responses for all primitive methods without network calls

#### Scenario: Fixture library for common test cases
- **WHEN** developer imports `aurelius.testing.fixtures`
- **THEN** SDK provides sample data (valid strategies, backtest results, gate configs) for test scenarios

### Requirement: Async/Await Support
The SDK SHALL provide async variants of all methods using `asyncio` for concurrent API calls in async applications.

#### Scenario: Async determinism scoring
- **WHEN** developer calls `await client.determinism.score_async(backtest_results)`
- **THEN** SDK uses async HTTP client (httpx.AsyncClient) and returns awaitable DeterminismScore

#### Scenario: Concurrent primitive calls
- **WHEN** developer uses `asyncio.gather()` to call multiple primitives concurrently
- **THEN** SDK executes requests in parallel and returns results in order

### Requirement: Response Caching for Read Operations
The SDK SHALL cache GET request responses (certification registry, gate definitions) for 5 minutes to reduce API calls.

#### Scenario: Cache gate definition query
- **WHEN** developer calls `client.gates.get_definition(gate_id)` twice within 5 minutes
- **THEN** SDK returns cached result on second call without API request

#### Scenario: Cache invalidation
- **WHEN** developer calls `client.cache.clear()` or 5 minutes elapse
- **THEN** SDK makes fresh API request on next method call

### Requirement: Comprehensive Error Handling
The SDK SHALL raise specific exception types for different error categories (authentication, validation, rate limiting, server errors) with actionable messages.

#### Scenario: Authentication error with fix suggestion
- **WHEN** API returns HTTP 401 due to invalid API key
- **THEN** SDK raises `AuthenticationError` with message "Invalid API key. Get your key at developers.aurelius.ai/keys"

#### Scenario: Rate limit error with retry guidance
- **WHEN** API returns HTTP 429 rate limit exceeded
- **THEN** SDK raises `RateLimitError` with `retry_after` timestamp and message "Rate limit exceeded. Retry after {timestamp}"

### Requirement: OpenAPI Code Generation Base
The SDK SHALL auto-generate base client code from OpenAPI specification to ensure API contract compliance.

#### Scenario: Sync with API updates
- **WHEN** API releases new primitive endpoint in OpenAPI spec
- **THEN** SDK CI pipeline regenerates client code and includes new method in next release

#### Scenario: Breaking change detection
- **WHEN** API introduces breaking change in OpenAPI spec (removed field, changed type)
- **THEN** SDK build fails with clear error message indicating incompatible change
