## Why

AURELIUS is currently positioned as a trading platform (workflow-oriented, dashboard-first) but the strategic vision is to be Financial Reasoning Infrastructure—a blue ocean play similar to Stripe for payments. The current monolithic architecture prevents external teams from composing our verification primitives into their own quant workflows. This refactor transforms AURELIUS from a platform into composable infrastructure, unlocking exponential adoption through API-first primitives, SDKs, and developer ecosystem.

## What Changes

- **Extract API Primitives**: Decompose 35+ workflow endpoints into 8-12 standalone infrastructure primitives (determinism scoring, risk validation, policy checking, strategy verification, acceptance evidence classification, gate verification, reflexion feedback, orchestration composition)
- **API-First Architecture**: RESTful primitives with OpenAPI specs, SDK client libraries (Python, JavaScript/TypeScript), webhook integrations, and embeddable components
- **Developer Portal**: Create developers.aurelius.ai with interactive docs, API explorer, code examples, integration guides, and certification registry
- **SDK & Tooling**: Official client libraries with type safety, retry logic, response caching, and local testing harness
- **Migration Path**: Maintain backward compatibility during transition, provide migration guides, deprecation timeline, and legacy endpoint support (12-month sunset)
- **Go-to-Market Repositioning**: Shift messaging from "trading platform for quants" to "financial reasoning infrastructure for fintech builders"

## Capabilities

### New Capabilities
- `api-primitive-determinism`: Standalone determinism scoring service exposing backtesting result consistency verification as an API primitive
- `api-primitive-risk`: Risk validation API for portfolio metrics verification (Sharpe, Sortino, max drawdown, VaR)
- `api-primitive-policy`: Policy compliance checking API for regulatory and business rule validation
- `api-primitive-strategy`: Strategy verification API for signal generation, parameter validation, and backtest orchestration
- `api-primitive-evidence`: Acceptance evidence classification API for freshness analysis and quality scoring
- `api-primitive-gates`: Gate verification API for production promotion readiness with configurable workflows
- `api-primitive-reflexion`: Reflexion feedback API for strategy improvement suggestions and constraint synthesis
- `api-primitive-orchestrator`: Orchestration composition API for multi-primitive workflow automation
- `developer-sdk-python`: Official Python SDK with type hints, async support, and testing utilities
- `developer-sdk-javascript`: Official JavaScript/TypeScript SDK with React hooks and Node.js support
- `developer-portal`: Interactive documentation site with API explorer, code generators, and certification registry
- `webhook-infrastructure`: Webhook delivery system for event-driven integration patterns
- `embeddable-components`: React/Vue embeddable UI components for verification results visualization

### Modified Capabilities
- `promotion-readiness-scorecard`: Refactor from internal workflow component to standalone API primitive with public contract
- `release-maturity-gates`: Extend gate system to support external integration and custom gate definitions
- `runtime-truth-path`: Expose operational health metrics as API endpoints for external monitoring
- `acceptance-evidence-quality`: Transform evidence parser into public API with classification taxonomy
- `documentation-reality-alignment`: Update all documentation to reflect API-first developer experience

## Impact

**Code Changes**:
- Major refactor of `api/` directory: Extract services into standalone primitive modules
- New `api/primitives/` directory with 8 primitive endpoint routers
- New `sdk/` directory with Python and JavaScript client libraries
- New `developer-portal/` directory with documentation site (Next.js)
- Dashboard migration to consume new primitive APIs instead of legacy endpoints

**Breaking Changes**:
- **BREAKING**: Existing workflow endpoints (`/api/v1/strategies/validate`, `/api/v1/backtests/verify`) will be deprecated in favor of primitive endpoints (`/api/primitives/v1/strategy/verify`, `/api/primitives/v1/determinism/score`)
- **BREAKING**: Response schemas standardized across primitives (canonical envelope: `{data, meta, links}`)
- **BREAKING**: Authentication flow changes to support API key-based access alongside JWT tokens

**Dependencies**:
- OpenAPI code generation tools (openapi-generator, swagger-codegen)
- SDK packaging infrastructure (PyPI for Python, npm for JavaScript)
- Developer portal framework (Next.js, MDX for docs)
- Webhook delivery infrastructure (event queue, retry logic, signature verification)

**Systems**:
- New deployment pipeline for SDK releases (versioning, changelog, breaking change detection)
- Developer portal hosting (Vercel or AWS Amplify)
- API gateway for rate limiting, usage tracking, and developer key management
- Monitoring and observability for primitive API performance metrics

**Timeline**: 20-24 weeks, 6-8 engineer team
