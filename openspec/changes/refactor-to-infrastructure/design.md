## Context

AURELIUS currently has 35+ API endpoints organized around workflow execution (strategy submission → backtest → validation → gate check → promotion). The FastAPI backend (`api/` directory) contains services that implement verification primitives (determinism scoring, risk validation, policy checks) but they are tightly coupled to the monolithic workflow orchestrator. The React dashboard (`dashboard/` directory) is the primary interface, designed for end-user quants rather than developer integration.

**Current Architecture:**
- Workflow-first: Endpoints like `/api/v1/strategies/{id}/validate` bundle multiple verification steps
- Monolithic services: `api/services/` contains logic but no clear primitive boundaries
- Dashboard-centric: UI components directly call workflow endpoints
- Internal-only: No public SDK, no developer documentation, no webhook infrastructure

**Strategic Context:**
The refactor enables a blue ocean positioning shift from "trading platform" to "financial reasoning infrastructure." This requires decomposing the workflow into composable primitives that external fintech builders can integrate into their own systems, similar to how Stripe provides payment primitives.

**Constraints:**
- Maintain backward compatibility for existing dashboard during transition (12-month deprecation window)
- No downtime deployment (blue-green strategy for API migration)
- Preserve all existing verification logic and accuracy
- Support both API key (for external developers) and JWT (for dashboard) authentication

**Stakeholders:**
- External developers integrating AURELIUS primitives (primary)
- Existing dashboard users (maintain continuity)
- Platform team (migration burden)

## Goals / Non-Goals

**Goals:**
- Extract 8 standalone API primitives with clear contracts (OpenAPI specs)
- Provide official SDKs (Python, JavaScript) with <100ms overhead vs raw HTTP
- Launch developer portal with interactive docs and certification registry
- Enable external teams to compose primitives into custom workflows
- Support both synchronous (REST) and asynchronous (webhook) integration patterns
- Achieve API-first architecture where dashboard becomes one client among many

**Non-Goals:**
- Complete rewrite of verification logic (preserve existing algorithms)
- GraphQL API (focus on RESTful primitives for simplicity)
- Multi-cloud deployment (stay AWS-focused for Phase 1)
- Free tier for developer portal (pricing strategy separate decision)
- Real-time streaming (WebSocket primitives deferred to Phase 2)

## Decisions

### Decision 1: API Primitive Boundaries
**Choice:** Extract 8 core primitives: determinism, risk, policy, strategy, evidence, gates, reflexion, orchestrator

**Rationale:** 
- Aligns with existing `api/services/` modules but with clearer contracts
- Each primitive has single responsibility and can evolve independently
- Orchestrator primitive allows composing multi-step workflows externally
- Matches mental model of "infrastructure building blocks"

**Alternatives Considered:**
- **12+ finer-grained primitives** (e.g., separate Sharpe ratio calculation): Too granular, increases integration complexity
- **5 coarse-grained primitives** (e.g., combine risk+policy into "validation"): Loses composability, harder to price independently
- **Domain-driven design with bounded contexts**: Over-architected for current scale

### Decision 2: API Versioning Strategy
**Choice:** URL-based versioning with `/api/primitives/v1/` namespace

**Rationale:**
- Clear separation between legacy workflow endpoints (`/api/v1/`) and new primitives (`/api/primitives/v1/`)
- URL versioning is simple for client caching and routing
- Enables gradual migration without breaking existing clients
- Standard practice for infrastructure APIs (Stripe, Twilio)

**Alternatives Considered:**
- **Header-based versioning** (`Accept: application/vnd.aurelius.v1+json`): More RESTful but harder to test/debug
- **No versioning with backward compatibility forever**: Technical debt accumulation risk
- **Separate subdomain** (`primitives.aurelius.ai`): Additional ops complexity

### Decision 3: SDK Architecture
**Choice:** Auto-generated base SDK from OpenAPI + hand-crafted convenience layer

**Rationale:**
- OpenAPI codegen ensures SDK stays in sync with API contract
- Hand-crafted layer provides idiomatic language experience (async/await, type hints, retry logic)
- Testing harness with mock responses enables local development without live API
- Balance between maintenance burden and developer experience

**Alternatives Considered:**
- **Fully hand-crafted SDK**: High maintenance, drift risk
- **Pure OpenAPI codegen**: Poor developer experience (verbose, not idiomatic)
- **Community-maintained SDKs only**: Slower adoption, quality variance

### Decision 4: Backward Compatibility Strategy
**Choice:** Legacy endpoints remain operational for 12 months with deprecation warnings, dashboard migrates to primitives in Phase 4

**Rationale:**
- Gives existing users time to migrate without disruption
- Dashboard migration validates primitive API design before external release
- Deprecation headers (`Sunset: Sat, 01 Mar 2027 00:00:00 GMT`) provide clear timeline
- Internal dogfooding catches issues before external developers encounter them

**Alternatives Considered:**
- **Immediate cutover**: Breaks existing integrations, high risk
- **Indefinite support**: Technical debt grows, harder to evolve
- **Proxy pattern** (legacy endpoints call primitives): Complexity, performance overhead

### Decision 5: Authentication Model
**Choice:** Dual authentication: API keys for external developers + JWT tokens for dashboard

**Rationale:**
- API keys simpler for server-to-server integration (no token refresh logic)
- JWT tokens better for browser-based dashboard (CSRF protection, short-lived)
- Both methods supported by FastAPI middleware without major refactor
- Standard pattern in infrastructure APIs (AWS IAM keys + temporary credentials)

**Alternatives Considered:**
- **OAuth 2.0 only**: Overkill for machine-to-machine API usage
- **API keys only**: Worse security for browser-based clients
- **mTLS certificates**: Too complex for initial adoption

### Decision 6: Developer Portal Technology
**Choice:** Next.js + MDX for documentation site, hosted on Vercel

**Rationale:**
- Next.js provides SSR for SEO (critical for developer discovery)
- MDX allows embedding interactive API examples in markdown docs
- Vercel deployment is zero-config with preview environments for PR reviews
- React components enable API explorer with live testing

**Alternatives Considered:**
- **Docusaurus**: Less flexible for custom API explorer components
- **Gatsby**: Slower build times, more complex configuration
- **Readme.io / Stoplight**: SaaS cost, less customization

### Decision 7: Migration Execution Order
**Choice:** Phase 1 (Primitives) → Phase 2 (SDK) → Phase 3 (Portal) → Phase 4 (Dashboard Migration) → Phase 5 (GTM)

**Rationale:**
- Primitives must exist before SDK can be built
- SDK needed for quality developer experience before portal launch
- Dashboard migration validates design before public release
- GTM messaging depends on proven external adoption

**Alternatives Considered:**
- **Big bang release**: Higher risk, harder to debug issues
- **Portal first, then primitives**: Misleading to show docs for non-existent APIs
- **Dashboard migration first**: Loses opportunity to dogfood before external launch

### Decision 8: Webhook Infrastructure
**Choice:** Event-driven webhooks with retry logic, signature verification, and delivery guarantees

**Rationale:**
- Long-running operations (backtests, complex verifications) need async patterns
- Reduces client polling overhead
- Standard infrastructure pattern (GitHub webhooks, Stripe events)
- Queue-based delivery (AWS SQS) provides retry and dead-letter handling

**Alternatives Considered:**
- **Polling-only**: Inefficient, poor developer experience for long operations
- **Server-sent events (SSE)**: Harder to implement reliably at scale
- **WebSocket streaming**: Overkill for batch operations, adds connection management complexity

## Risks / Trade-offs

### Risk: API Primitive Design Flaws Not Caught Until External Usage
**Impact:** Breaking changes after external adoption damage trust

**Mitigation:** 
- Internal dashboard migration in Phase 4 dogfoods primitive APIs before public launch
- Private beta with 3-5 partner teams (Alpha Vantage, Interactive Brokers, QuantConnect) to validate design
- Versioned APIs allow fixing mistakes in v2 without breaking v1
- Comprehensive OpenAPI specs reviewed by external architects before implementation

### Risk: SDK Maintenance Burden Across Multiple Languages
**Impact:** SDKs fall out of sync with API, poor developer experience

**Mitigation:**
- OpenAPI codegen automates 80% of SDK generation
- CI/CD pipeline runs SDK tests against live API daily
- Initial launch with 2 SDKs only (Python, JavaScript)—add more based on demand
- Community contribution guide for additional language SDKs

### Risk: Migration Complexity Causes Dashboard Regressions
**Impact:** Existing users experience bugs during transition

**Mitigation:**
- Feature flag system allows gradual rollout (10% → 50% → 100% traffic)
- Comprehensive regression test suite (existing 28 tests + new primitive contract tests)
- 12-month deprecation window provides rollback safety net
- Monitoring dashboard tracks error rates for legacy vs primitive endpoints

### Risk: Developer Portal Content Becomes Stale
**Impact:** Outdated docs frustrate developers, slow adoption

**Mitigation:**
- OpenAPI specs as single source of truth (docs auto-generated from schemas)
- SDK code examples extracted from integration tests (always working)
- Monthly doc review process with external developer feedback
- Versioned docs site preserves old versions (developers.aurelius.ai/v1/, /v2/)

### Risk: Webhook Delivery Failures Create Silent Errors
**Impact:** Developers miss critical verification results, trust erosion

**Mitigation:**
- Exponential backoff retry logic (10 attempts over 24 hours)
- Dead-letter queue captures failed events for manual investigation
- Dashboard visibility into webhook delivery status per developer key
- HMAC signature verification prevents spoofing/replay attacks

### Risk: Authentication Dual Model Increases Attack Surface
**Impact:** Security vulnerabilities in API key or JWT handling

**Mitigation:**
- API keys stored hashed (bcrypt) with rate limiting per key
- JWT tokens short-lived (15 minutes) with secure refresh flow
- Separate middleware layers for each auth method (fail-safe isolation)
- Regular security audits (OWASP Top 10 checklist)
- API key rotation enforcement (90-day expiry)

### Trade-off: Backward Compatibility Prolongs Monolith Maintenance
**Cost:** 12 months of dual endpoint support increases operational complexity

**Benefit:** Zero-downtime migration path, user trust maintained

**Decision:** Accept cost—infrastructure positioning requires smooth transition to build developer trust

### Trade-off: OpenAPI Codegen vs Hand-crafted SDKs
**Cost:** Generated code less idiomatic, requires wrapper layer

**Benefit:** Automatic sync with API changes, reduced maintenance

**Decision:** Hybrid approach—generated base + hand-crafted convenience layer balances both

## Migration Plan

### Phase 1: API Primitive Extraction (Weeks 1-8)
1. Create `/api/primitives/v1/` router structure with 8 endpoint modules
2. Extract logic from existing `api/services/` into primitive handlers
3. Define OpenAPI specs for each primitive (request/response schemas)
4. Implement primitive endpoints with isolated unit tests
5. Deploy primitives to staging environment with feature flags disabled
6. Validate performance (latency <200ms for sync operations)

**Rollback:** Feature flags allow reverting to legacy endpoints without code deployment

### Phase 2: SDK Development (Weeks 9-14)
1. Generate base SDK code from OpenAPI specs (Python, JavaScript)
2. Add convenience layer (retry logic, type hints, testing utilities)
3. Publish SDK to private package repositories (internal PyPI, npm registry)
4. Write integration tests using SDKs against staging primitives
5. Internal team validation (platform team uses SDKs for 2 weeks)
6. Fix SDK issues identified in validation period

**Rollback:** Private packages prevent external access if critical bugs found

### Phase 3: Developer Portal (Weeks 15-20)
1. Set up Next.js project structure (`developer-portal/`)
2. Create MDX documentation pages for each primitive with code examples
3. Build interactive API explorer (test requests directly from docs)
4. Implement certification registry (track which developers passed integration tests)
5. Deploy to staging (staging.developers.aurelius.ai)
6. Beta test with 3-5 partner teams, iterate based on feedback

**Rollback:** Staging deployment isolates issues, production launch separate decision

### Phase 4: Dashboard Migration (Weeks 21-26)
1. Feature flag 10% of dashboard traffic to use primitive APIs instead of legacy
2. Monitor error rates, latency, and user feedback for regressions
3. Gradually increase traffic: 10% → 25% → 50% → 100% over 4 weeks
4. Deprecate legacy endpoints (add `Sunset` headers with 12-month timeline)
5. Update dashboard monitoring to track primitive API health
6. Document migration guide for any remaining custom integrations

**Rollback:** Feature flags allow instant revert to legacy endpoints if P0 issues

### Phase 5: Public Launch & GTM (Weeks 27+)
1. Publish SDKs to public repositories (PyPI, npm)
2. Launch developer portal at developers.aurelius.ai
3. Announce infrastructure positioning with case studies from beta partners
4. Sales/marketing campaign: "Stripe for Financial Reasoning"
5. Monitor adoption metrics (API key registrations, SDK downloads, webhook usage)
6. Iterate on primitives based on external developer feedback

**Rollback:** None (public launch irreversible)—emphasize quality before this phase

### Deployment Strategy
- **Blue-Green Deployment:** New primitive API version deployed to separate cluster, traffic switched after validation
- **Database Compatibility:** Schema changes backward-compatible (additive columns only)
- **Monitoring:** New Datadog dashboard tracking primitive API metrics (latency, error rate, usage per primitive)
- **Alerts:** PagerDuty integration for P0 issues (error rate >1%, latency >500ms)

### Success Metrics
- **Week 8:** All 8 primitives passing contract tests (100% spec compliance)
- **Week 14:** SDKs achieving <100ms overhead vs raw HTTP requests
- **Week 20:** Developer portal live with 5 partner teams onboarded
- **Week 26:** Dashboard fully migrated (0% legacy endpoint usage)
- **Month 12:** 50+ external integrations, 10K+ API calls/day

## Open Questions

1. **Pricing Model for API Access:** Per-request metering vs monthly tiers? Decision needed by Week 20 (portal launch)
2. **SLA Guarantees:** What uptime % do we commit to for primitives? (99.9% requires additional infrastructure)
3. **Rate Limiting Strategy:** Per API key? Per primitive? Global throttle? Affects SDK design
4. **Multi-Region Deployment:** When do we expand beyond AWS us-east-1? (Latency concerns for international developers)
5. **GraphQL Gateway:** Do we add GraphQL layer in future for complex queries? (Deferred to Phase 2 but affects primitive design)
6. **Certification Program:** What tests must developers pass to get "AURELIUS Certified" badge? (Affects portal requirements)

**Resolution Timeline:** Resolve questions 1-3 by Week 15 (before portal design finalized), questions 4-6 can wait until post-launch feedback
