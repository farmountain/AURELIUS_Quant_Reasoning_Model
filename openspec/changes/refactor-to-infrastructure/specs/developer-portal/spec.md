## ADDED Requirements

### Requirement: Interactive Documentation Site
The system SHALL provide a developer portal at developers.aurelius.ai with interactive API documentation, code examples, and integration guides for all primitives.

#### Scenario: Browse primitive API docs
- **WHEN** developer visits developers.aurelius.ai/docs/primitives/determinism
- **THEN** site displays OpenAPI-generated documentation with request/response schemas, authentication requirements, and error codes

#### Scenario: Try API in browser
- **WHEN** developer enters API key and test data in interactive explorer
- **THEN** site makes live API call and displays formatted response with syntax highlighting

### Requirement: Code Generator for Multiple Languages
The portal SHALL provide code snippet generator that converts API examples to Python, JavaScript, cURL, and HTTP syntax.

#### Scenario: Generate Python code example
- **WHEN** developer selects "Python" tab in documentation for determinism scoring endpoint
- **THEN** site displays runnable Python code using official SDK with example data

#### Scenario: Copy code to clipboard
- **WHEN** developer clicks "Copy" button on code snippet
- **THEN** site copies code to clipboard with import statements and error handling included

### Requirement: Certification Registry Public View
The portal SHALL display public certification registry showing strategies that passed production gates with verification scores and timestamps.

#### Scenario: View certified strategies
- **WHEN** developer visits developers.aurelius.ai/registry
- **THEN** site displays searchable table of certified strategies with gate scores, certification dates, and organization names (if public)

#### Scenario: Embed certification badge
- **WHEN** developer clicks "Get Badge" on certified strategy
- **THEN** site provides embeddable HTML/Markdown snippet with badge image and verification link

### Requirement: API Key Management Dashboard
The portal SHALL provide authenticated dashboard for managing API keys with usage analytics and rate limit monitoring.

#### Scenario: Generate new API key
- **WHEN** developer logs in and clicks "Create API Key"
- **THEN** site generates new key, displays it once with copy button, and shows key metadata (created date, permissions)

#### Scenario: View usage analytics
- **WHEN** developer views API key details
- **THEN** site displays usage charts (requests per day, primitives used, error rates, latency percentiles)

#### Scenario: Revoke API key
- **WHEN** developer clicks "Revoke" on API key
- **THEN** site immediately invalidates key and all subsequent requests return HTTP 401

### Requirement: Integration Guides and Tutorials
The portal SHALL provide step-by-step tutorials for common integration patterns with runnable code examples.

#### Scenario: Quickstart tutorial
- **WHEN** developer follows "5-Minute Quickstart" guide
- **THEN** tutorial walks through API key setup, SDK installation, and first primitive call with working code

#### Scenario: Webhook integration guide
- **WHEN** developer accesses webhook documentation
- **THEN** guide provides example webhook receiver code (Python Flask, Node Express) with signature verification

### Requirement: Search and Navigation
The portal SHALL provide full-text search across all documentation with instant results and keyboard navigation.

#### Scenario: Search for API method
- **WHEN** developer types "determinism score" in search box
- **THEN** site displays matching pages (API reference, integration guide, SDK docs) with highlighted excerpts

#### Scenario: Keyboard shortcuts
- **WHEN** developer presses "/" key
- **THEN** site focuses search input for quick navigation

### Requirement: Versioned Documentation
The portal SHALL maintain documentation for all API versions (v1, v2) with clear deprecation notices and migration guides.

#### Scenario: View legacy v1 docs
- **WHEN** developer selects "v1" from version dropdown
- **THEN** site displays v1 API documentation with deprecation banner linking to v2 migration guide

#### Scenario: Breaking change migration path
- **WHEN** developer accesses migration guide for v1 to v2
- **THEN** guide provides side-by-side comparison of changed endpoints with code examples for both versions

### Requirement: Performance and Accessibility
The portal SHALL load documentation pages in <2 seconds (p95) and meet WCAG 2.1 Level AA accessibility standards.

#### Scenario: Fast page load
- **WHEN** developer navigates to any documentation page
- **THEN** site renders interactive content within 2 seconds on average broadband connection

#### Scenario: Screen reader compatibility
- **WHEN** developer uses screen reader to navigate portal
- **THEN** site provides semantic HTML with ARIA labels for all interactive elements
