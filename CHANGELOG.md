# Changelog

All notable changes to the AURELIUS Quant Reasoning Model project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Integration test suite with 10 comprehensive tests for API validation
- WebSocket support for real-time strategy generation and backtest updates
- JWT authentication for all protected API endpoints
- Strategy ID tracking in responses for backtest execution
- PostgreSQL database integration for persistent storage

### Changed
- Strategy generation endpoint now requires authentication
- Backtest execution endpoint now requires authentication
- List strategies endpoint now requires authentication
- WebSocket connection now accepts both `/ws` and `/ws/` routes
- Strategy response schema now includes `id` field for reference

### Fixed
- WebSocket indentation and routing issues (403 errors resolved)
- Authentication middleware properly enforces JWT tokens on protected routes
- Integration tests now generate valid strategy IDs before running backtests
- Removed unused imports and fixed code style issues (ruff linting)
- Fixed bare `except` clauses to use `Exception` explicitly

## [1.0.0] - 2026-02-01

### Added
- Complete Python orchestrator for AURELIUS Quant Reasoning Model
- Tool API wrappers with JSON schema validation (8 tool types)
- Goal-Guard FSM with 11 states enforcing valid tool sequences
- Dual-loop evidence gates (Dev Gate and Product Gate)
- Reflexion loop for automatic failure recovery
- Strict mode enforcing artifact ID-only responses
- CLI interface (`aureus run --goal "..."`)
- 42 comprehensive unit tests (100% passing)
- REST API with FastAPI for strategy generation and backtesting
- HipCortex integration for audit trail and reproducibility

### Security
- CodeQL analysis showing 0 vulnerabilities
- SHA-256 cryptographic hashing for artifact IDs
- No hardcoded credentials
- Proper input validation with Pydantic
- Safe subprocess execution

### Documentation
- Complete usage guide (`python/README.md`)
- Integration test documentation
- Implementation summary
- Example scripts and workflows

---

## Version History

- **1.0.0** (2026-02-01): Initial release with complete orchestrator and API
- **Current** (2026-02-04): Authentication fixes, WebSocket improvements, and integration testing
