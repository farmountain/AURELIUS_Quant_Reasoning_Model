# Strategy, Evidence, and Reflexion API Documentation

This guide documents the **Strategy Verification**, **Evidence Classification**, and **Reflexion Feedback** primitives, three core APIs for validating trading strategies, classifying acceptance evidence, and generating improvement suggestions.

## Table of Contents

1. [Overview](#overview)
2. [Strategy Verification Primitive](#strategy-verification-primitive)
3. [Evidence Classification Primitive](#evidence-classification-primitive)
4. [Reflexion Feedback Primitive](#reflexion-feedback-primitive)
5. [Integrated Workflow Example](#integrated-workflow-example)
6. [Authentication](#authentication)
7. [Error Handling](#error-handling)
8. [Rate Limits](#rate-limits)

## Overview

These three primitives work together to support the strategy development and promotion lifecycle:

- **Strategy Verification**: Validates strategy parameters against type-specific rules and business logic
- **Evidence Classification**: Classifies acceptance evidence (backtests, gate checks, validation results) for promotion readiness
- **Reflexion Feedback**: Generates prioritized improvement suggestions based on performance metrics and feedback

**Base URL**: `http://localhost:8000/api/primitives/v1`

**Authentication**: All endpoints require either JWT token or API key authentication

**Feature Flags**: Each primitive can be enabled/disabled via feature flags:
- `ENABLE_PRIMITIVE_STRATEGY`
- `ENABLE_PRIMITIVE_EVIDENCE`
- `ENABLE_PRIMITIVE_REFLEXION`

## Strategy Verification Primitive

The Strategy Verification primitive validates trading strategy configurations against parameter rules and business logic constraints.

### Endpoint

```
POST /api/primitives/v1/strategy/verify
GET  /api/primitives/v1/strategy/health
```

### Supported Strategy Types

1. **momentum**: Trend-following strategies based on price momentum
2. **mean_reversion**: Mean-reverting strategies based on statistical deviations
3. **trend_following**: Dual moving average crossover strategies
4. **pairs_trading**: Statistical arbitrage between correlated pairs
5. **volatility_trading**: Volatility targeting and risk parity strategies
6. **ml_classifier**: Machine learning-based classification strategies

### Request Schema

```json
{
  "strategy_id": "string",
  "strategy_type": "momentum|mean_reversion|trend_following|pairs_trading|volatility_trading|ml_classifier",
  "parameters": {
    // Strategy-specific parameters (see examples below)
  },
  "context": {
    // Optional context for additional validation
  }
}
```

### Response Schema

```json
{
  "data": {
    "strategy_id": "string",
    "valid": true,
    "validation_score": 85,
    "passed_checks": ["check1", "check2"],
    "failed_checks": ["check3"],
    "warnings": ["warning1"],
    "details": {
      "total_checks": 10,
      "passed": 8,
      "failed": 2,
      "timestamp": "2024-01-15T10:30:00Z"
    }
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "primitive": "strategy"
  },
  "links": {
    "self": "/api/primitives/v1/strategy/verify"
  }
}
```

### Parameter Rules by Strategy Type

#### Momentum Strategy

```json
{
  "lookback": 20,           // Range: [5, 500], Required
  "threshold": 0.02,        // Range: [0, 1], Required
  "vol_target": 0.15,       // Range: [0, 1], Optional
  "stop_loss": 0.05,        // Range: [0, 1], Optional
  "take_profit": 0.10       // Range: [0, 1], Optional
}
```

**Business Rules**:
- `stop_loss < take_profit` (if both provided)
- `take_profit / stop_loss >= 1.5` (recommended)

#### Mean Reversion Strategy

```json
{
  "lookback": 20,           // Range: [5, 500], Required
  "entry_threshold": -2.0,  // Range: [-5, 0], Required
  "exit_threshold": -0.5,   // Range: [-2, 0], Required
  "vol_target": 0.10,       // Range: [0, 1], Optional
  "stop_loss": 0.03         // Range: [0, 1], Optional
}
```

**Business Rules**:
- `exit_threshold > entry_threshold` (exit closer to mean)

#### Trend Following Strategy

```json
{
  "fast_window": 10,        // Range: [2, 200], Required
  "slow_window": 50,        // Range: [5, 500], Required
  "vol_target": 0.15,       // Range: [0, 1], Optional
  "stop_loss": 0.05         // Range: [0, 1], Optional
}
```

**Business Rules**:
- `fast_window < slow_window` (fast must be shorter)

#### Pairs Trading Strategy

```json
{
  "lookback": 60,           // Range: [20, 500], Required
  "entry_threshold": 2.0,   // Range: [0.5, 5], Required
  "exit_threshold": 0.5,    // Range: [0, 2], Required
  "hedge_ratio": 1.0,       // Range: [0.1, 10], Optional
  "stop_loss": 0.05         // Range: [0, 1], Optional
}
```

**Business Rules**:
- `exit_threshold < entry_threshold`

#### Volatility Trading Strategy

```json
{
  "vol_target": 0.15,       // Range: [0.01, 1], Required
  "rebalance_freq": "daily", // Values: ["daily", "weekly", "monthly"], Required
  "lookback": 20,           // Range: [5, 252], Optional
  "leverage": 1.0           // Range: [0.1, 3], Optional
}
```

#### ML Classifier Strategy

```json
{
  "model_type": "random_forest", // Values: ["random_forest", "gradient_boost", "neural_net"], Required
  "lookback": 20,               // Range: [5, 500], Required
  "threshold": 0.5,             // Range: [0, 1], Required
  "retrain_freq": "monthly",    // Values: ["daily", "weekly", "monthly"], Optional
  "feature_count": 10           // Range: [1, 100], Optional
}
```

### Examples

#### Python SDK Example

```python
import requests

# Configuration
API_URL = "http://localhost:8000/api/primitives/v1/strategy/verify"
JWT_TOKEN = "your_jwt_token_here"

# Verify momentum strategy
payload = {
    "strategy_id": "momentum_001",
    "strategy_type": "momentum",
    "parameters": {
        "lookback": 20,
        "threshold": 0.02,
        "vol_target": 0.15,
        "stop_loss": 0.05,
        "take_profit": 0.10
    }
}

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

response = requests.post(API_URL, json=payload, headers=headers)
result = response.json()

if result["data"]["valid"]:
    print(f"Strategy valid with score: {result['data']['validation_score']}")
else:
    print(f"Strategy invalid: {result['data']['failed_checks']}")
    print(f"Warnings: {result['data']['warnings']}")
```

#### cURL Example

```bash
curl -X POST "http://localhost:8000/api/primitives/v1/strategy/verify" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "mean_rev_001",
    "strategy_type": "mean_reversion",
    "parameters": {
      "lookback": 20,
      "entry_threshold": -2.0,
      "exit_threshold": -0.5,
      "vol_target": 0.10
    }
  }'
```

#### JavaScript/TypeScript Example

```typescript
interface StrategyVerifyRequest {
  strategy_id: string;
  strategy_type: string;
  parameters: Record<string, any>;
  context?: Record<string, any>;
}

async function verifyStrategy(request: StrategyVerifyRequest): Promise<any> {
  const response = await fetch('http://localhost:8000/api/primitives/v1/strategy/verify', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${JWT_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Strategy verification failed: ${response.statusText}`);
  }

  return await response.json();
}

// Usage
const result = await verifyStrategy({
  strategy_id: 'trend_001',
  strategy_type: 'trend_following',
  parameters: {
    fast_window: 10,
    slow_window: 50,
    vol_target: 0.15
  }
});

console.log(`Valid: ${result.data.valid}, Score: ${result.data.validation_score}`);
```

## Evidence Classification Primitive

The Evidence Classification primitive classifies acceptance evidence for strategy promotion decisions.

### Endpoint

```
POST /api/primitives/v1/evidence/classify
GET  /api/primitives/v1/evidence/health
```

### Supported Evidence Types

1. **backtest**: Historical simulation results
2. **validation**: Walk-forward validation results
3. **gate_check**: Gate verification status codes
4. **acceptance_test**: Acceptance test results
5. **production_metrics**: Live production performance metrics
6. **custom**: User-defined evidence types

### Classification Categories

- **contract-valid-success**: Evidence meets contract and shows success
- **contract-valid-failure**: Evidence meets contract but shows failure
- **contract-invalid-failure**: Evidence fails to meet contract requirements
- **mixed**: Mixed success and failure signals
- **stale**: Evidence is too old (exceeds max_age_hours)
- **incomplete**: Evidence missing required fields
- **valid**: General valid evidence (for non-gate types)

### Request Schema

```json
{
  "evidence_id": "string",
  "evidence_type": "backtest|validation|gate_check|acceptance_test|production_metrics|custom",
  "data": {
    // Evidence-specific data (see examples below)
  },
  "timestamp": "2024-01-15T10:30:00Z",  // ISO 8601 format
  "max_age_hours": 24                   // Optional, default: 24
}
```

### Response Schema

```json
{
  "data": {
    "evidence_id": "string",
    "classification": "contract-valid-success",
    "confidence": 0.95,
    "completeness_score": 85,
    "details": {
      "is_fresh": true,
      "age_hours": 2.5,
      "quality_indicators": {
        "has_metrics": true,
        "has_timestamp": true,
        "has_required_fields": true
      },
      "missing_fields": [],
      "warnings": []
    }
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "primitive": "evidence"
  },
  "links": {
    "self": "/api/primitives/v1/evidence/classify"
  }
}
```

### Evidence Data Schemas by Type

#### Gate Check Evidence

```json
{
  "dev_status": 200,        // HTTP status code from dev gate
  "crv_status": 200,        // HTTP status code from crv gate
  "product_status": 200,    // HTTP status code from product gate
  "environment": "staging"  // Optional
}
```

**Classification Logic**:
- All 200 → `contract-valid-success` (confidence: 1.0)
- Dev 200, others 404/422 → `contract-valid-failure` (confidence: 0.9)
- Any 500+ → `contract-invalid-failure` (confidence: 0.7)
- Mixed results → `mixed` (confidence: 0.5)

#### Backtest Evidence

```json
{
  "sharpe_ratio": 1.5,
  "max_drawdown": 0.15,
  "total_return": 0.25,
  "num_trades": 50,
  "win_rate": 0.55          // Optional
}
```

**Classification Logic**:
- Sharpe >= 1.0, drawdown <= 0.20 → `valid`
- Otherwise → `contract-valid-failure`
- Missing fields → `incomplete`

#### Validation Evidence

```json
{
  "status": "completed",    // "completed", "failed", "pending"
  "metrics": {
    "avg_sharpe": 1.2,
    "consistency": 0.8
  }
}
```

#### Production Metrics Evidence

```json
{
  "uptime": 0.999,
  "error_rate": 0.001,
  "latency_p95": 150,       // milliseconds
  "throughput": 1000        // req/sec
}
```

**Classification Logic**:
- Uptime >= 0.99, error_rate <= 0.01, latency_p95 <= 500 → `valid`
- Otherwise → `contract-valid-failure`

### Examples

#### Python SDK Example

```python
import requests
from datetime import datetime, timezone

API_URL = "http://localhost:8000/api/primitives/v1/evidence/classify"
JWT_TOKEN = "your_jwt_token_here"

# Classify gate check evidence
payload = {
    "evidence_id": "gate_staging_001",
    "evidence_type": "gate_check",
    "data": {
        "dev_status": 200,
        "crv_status": 200,
        "product_status": 200,
        "environment": "staging"
    },
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "max_age_hours": 24
}

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

response = requests.post(API_URL, json=payload, headers=headers)
result = response.json()

print(f"Classification: {result['data']['classification']}")
print(f"Confidence: {result['data']['confidence']}")
print(f"Completeness: {result['data']['completeness_score']}")

if not result['data']['details']['is_fresh']:
    print("Warning: Evidence is stale")
```

#### cURL Example

```bash
curl -X POST "http://localhost:8000/api/primitives/v1/evidence/classify" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "evidence_id": "backtest_001",
    "evidence_type": "backtest",
    "data": {
      "sharpe_ratio": 1.5,
      "max_drawdown": 0.15,
      "total_return": 0.25,
      "num_trades": 50
    },
    "timestamp": "2024-01-15T10:30:00Z"
  }'
```

#### JavaScript/TypeScript Example

```typescript
interface EvidenceClassifyRequest {
  evidence_id: string;
  evidence_type: string;
  data: Record<string, any>;
  timestamp?: string;
  max_age_hours?: number;
}

async function classifyEvidence(request: EvidenceClassifyRequest): Promise<any> {
  const response = await fetch('http://localhost:8000/api/primitives/v1/evidence/classify', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${JWT_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      ...request,
      timestamp: request.timestamp || new Date().toISOString(),
    }),
  });

  if (!response.ok) {
    throw new Error(`Evidence classification failed: ${response.statusText}`);
  }

  return await response.json();
}

// Usage
const result = await classifyEvidence({
  evidence_id: 'prod_metrics_001',
  evidence_type: 'production_metrics',
  data: {
    uptime: 0.999,
    error_rate: 0.001,
    latency_p95: 150
  }
});

console.log(`Classification: ${result.data.classification}`);
console.log(`Confidence: ${result.data.confidence}`);
```

## Reflexion Feedback Primitive

The Reflexion Feedback primitive generates improvement suggestions based on strategy performance and feedback.

### Endpoint

```
POST /api/primitives/v1/reflexion/suggest
GET  /api/primitives/v1/reflexion/health
```

### Request Schema

```json
{
  "strategy_id": "string",
  "strategy_type": "momentum|mean_reversion|...",
  "parameters": {
    // Current strategy parameters
  },
  "performance_metrics": {
    "sharpe_ratio": 1.0,
    "max_drawdown": 0.15,
    "win_rate": 0.55,
    // Other metrics...
  },
  "feedback": "Optional human feedback text",
  "context": {
    // Optional additional context
  }
}
```

### Response Schema

```json
{
  "data": {
    "strategy_id": "string",
    "improvement_score": -1.5,
    "suggestions": [
      {
        "suggestion": "Increase lookback period to reduce noise",
        "category": "parameter",
        "priority": "high"
      }
    ],
    "summary": "Strategy shows moderate improvement potential"
  },
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "primitive": "reflexion"
  },
  "links": {
    "self": "/api/primitives/v1/reflexion/suggest"
  }
}
```

### Improvement Score

The improvement score ranges from **-2.0** (needs major improvements) to **+2.0** (excellent performance):

- **-2.0 to -1.0**: Poor performance, major changes needed
- **-1.0 to 0.0**: Below average, improvements recommended
- **0.0 to +1.0**: Average to good performance
- **+1.0 to +2.0**: Excellent performance, minor optimizations

Score is **deterministic** based on strategy_id hash for consistency.

### Suggestion Categories

1. **parameter**: Parameter tuning suggestions
2. **logic**: Strategy logic improvements
3. **risk_management**: Risk control enhancements
4. **timing**: Execution timing optimizations

### Suggestion Priorities

1. **high**: Critical improvements (e.g., Sharpe < 0.5, drawdown > 0.30)
2. **medium**: Recommended improvements (e.g., Sharpe < 1.0, drawdown > 0.20)
3. **low**: Optional optimizations

### Suggestion Generation Logic

#### Metric-Based Suggestions

- **Low Sharpe (< 1.0)**: Suggest parameter tuning, risk management
- **High Drawdown (> 0.20)**: Suggest stop loss, position sizing
- **Low Win Rate (< 0.45)**: Suggest entry/exit logic improvements

#### Feedback-Based Suggestions

Keywords in feedback trigger specific suggestions:
- "volatility" → Volatility targeting suggestions
- "drawdown" → Risk management suggestions
- "timing" → Execution timing suggestions
- "whipsaw" → Parameter smoothing suggestions

#### Context-Aware Suggestions

Strategy type-specific suggestions:
- **Momentum**: Trend strength filters, volatility scaling
- **Mean Reversion**: Threshold optimization, regime filters
- **Trend Following**: Window optimization, breakout confirmation
- **Pairs Trading**: Cointegration monitoring, hedge ratio adjustment

### Examples

#### Python SDK Example

```python
import requests

API_URL = "http://localhost:8000/api/primitives/v1/reflexion/suggest"
JWT_TOKEN = "your_jwt_token_here"

# Get improvement suggestions
payload = {
    "strategy_id": "momentum_001",
    "strategy_type": "momentum",
    "parameters": {
        "lookback": 20,
        "threshold": 0.02
    },
    "performance_metrics": {
        "sharpe_ratio": 0.8,
        "max_drawdown": 0.25,
        "win_rate": 0.48
    },
    "feedback": "Strategy shows high volatility during market stress"
}

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

response = requests.post(API_URL, json=payload, headers=headers)
result = response.json()

print(f"Improvement Score: {result['data']['improvement_score']}")
print(f"Summary: {result['data']['summary']}")
print("\nSuggestions:")
for suggestion in result['data']['suggestions']:
    print(f"[{suggestion['priority'].upper()}] {suggestion['category']}: {suggestion['suggestion']}")
```

#### cURL Example

```bash
curl -X POST "http://localhost:8000/api/primitives/v1/reflexion/suggest" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_id": "mean_rev_001",
    "strategy_type": "mean_reversion",
    "parameters": {
      "lookback": 20,
      "entry_threshold": -2.0
    },
    "performance_metrics": {
      "sharpe_ratio": 1.2,
      "max_drawdown": 0.18
    }
  }'
```

#### JavaScript/TypeScript Example

```typescript
interface ReflexionSuggestRequest {
  strategy_id: string;
  strategy_type: string;
  parameters: Record<string, any>;
  performance_metrics: Record<string, number>;
  feedback?: string;
  context?: Record<string, any>;
}

async function getSuggestions(request: ReflexionSuggestRequest): Promise<any> {
  const response = await fetch('http://localhost:8000/api/primitives/v1/reflexion/suggest', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${JWT_TOKEN}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    throw new Error(`Reflexion suggestion failed: ${response.statusText}`);
  }

  return await response.json();
}

// Usage
const result = await getSuggestions({
  strategy_id: 'pairs_001',
  strategy_type: 'pairs_trading',
  parameters: {
    lookback: 60,
    entry_threshold: 2.0
  },
  performance_metrics: {
    sharpe_ratio: 0.7,
    max_drawdown: 0.22
  }
});

// Filter high-priority suggestions
const highPriority = result.data.suggestions.filter(s => s.priority === 'high');
console.log('Critical improvements:', highPriority);
```

## Integrated Workflow Example

This example demonstrates using all three primitives together for a complete strategy validation workflow.

### Python End-to-End Example

```python
import requests
from datetime import datetime, timezone

BASE_URL = "http://localhost:8000/api/primitives/v1"
JWT_TOKEN = "your_jwt_token_here"

headers = {
    "Authorization": f"Bearer {JWT_TOKEN}",
    "Content-Type": "application/json"
}

# Step 1: Verify strategy parameters
strategy_payload = {
    "strategy_id": "momentum_prod_001",
    "strategy_type": "momentum",
    "parameters": {
        "lookback": 20,
        "threshold": 0.02,
        "vol_target": 0.15,
        "stop_loss": 0.05,
        "take_profit": 0.10
    }
}

strategy_response = requests.post(
    f"{BASE_URL}/strategy/verify",
    json=strategy_payload,
    headers=headers
)

if not strategy_response.json()["data"]["valid"]:
    print("Strategy validation failed!")
    print(strategy_response.json()["data"]["failed_checks"])
    exit(1)

print("✓ Strategy parameters validated")

# Step 2: Classify backtest evidence
backtest_payload = {
    "evidence_id": "backtest_momentum_001",
    "evidence_type": "backtest",
    "data": {
        "sharpe_ratio": 1.2,
        "max_drawdown": 0.18,
        "total_return": 0.30,
        "num_trades": 75,
        "win_rate": 0.52
    },
    "timestamp": datetime.now(timezone.utc).isoformat()
}

backtest_response = requests.post(
    f"{BASE_URL}/evidence/classify",
    json=backtest_payload,
    headers=headers
)

backtest_result = backtest_response.json()["data"]
print(f"✓ Backtest evidence: {backtest_result['classification']}")
print(f"  Confidence: {backtest_result['confidence']}")

# Step 3: Classify gate check evidence
gate_payload = {
    "evidence_id": "gate_staging_001",
    "evidence_type": "gate_check",
    "data": {
        "dev_status": 200,
        "crv_status": 200,
        "product_status": 200,
        "environment": "staging"
    },
    "timestamp": datetime.now(timezone.utc).isoformat()
}

gate_response = requests.post(
    f"{BASE_URL}/evidence/classify",
    json=gate_payload,
    headers=headers
)

gate_result = gate_response.json()["data"]
print(f"✓ Gate check: {gate_result['classification']}")

# Step 4: Get improvement suggestions
reflexion_payload = {
    "strategy_id": "momentum_prod_001",
    "strategy_type": "momentum",
    "parameters": strategy_payload["parameters"],
    "performance_metrics": {
        "sharpe_ratio": backtest_payload["data"]["sharpe_ratio"],
        "max_drawdown": backtest_payload["data"]["max_drawdown"],
        "win_rate": backtest_payload["data"]["win_rate"]
    },
    "feedback": "Strategy performs well but has occasional whipsaw trades"
}

reflexion_response = requests.post(
    f"{BASE_URL}/reflexion/suggest",
    json=reflexion_payload,
    headers=headers
)

reflexion_result = reflexion_response.json()["data"]
print(f"✓ Improvement score: {reflexion_result['improvement_score']}")
print(f"  Summary: {reflexion_result['summary']}")
print("\n  High-priority suggestions:")
for suggestion in reflexion_result["suggestions"]:
    if suggestion["priority"] == "high":
        print(f"    - {suggestion['suggestion']}")

# Step 5: Make promotion decision
can_promote = (
    strategy_response.json()["data"]["valid"] and
    backtest_result["classification"] in ["valid", "contract-valid-success"] and
    gate_result["classification"] == "contract-valid-success" and
    reflexion_result["improvement_score"] > -0.5
)

if can_promote:
    print("\n✅ Strategy approved for promotion to production")
else:
    print("\n❌ Strategy requires improvements before promotion")
```

## Authentication

All primitive endpoints require authentication using either:

### JWT Token Authentication

```python
headers = {
    "Authorization": f"Bearer {jwt_token}",
    "Content-Type": "application/json"
}
```

**Rate Limit**: 5000 requests/hour

### API Key Authentication

```python
headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}
```

**Rate Limit**: 1000 requests/hour

### Obtaining Credentials

**JWT Token**:
```python
response = requests.post(
    "http://localhost:8000/api/v1/auth/token",
    json={"username": "user", "password": "pass"}
)
jwt_token = response.json()["access_token"]
```

**API Key**: Contact administrator for API key provisioning.

## Error Handling

All primitives use consistent error responses:

### Error Response Schema

```json
{
  "detail": "Error message",
  "meta": {
    "timestamp": "2024-01-15T10:30:00Z",
    "primitive": "strategy|evidence|reflexion"
  }
}
```

### Common Status Codes

- **200**: Success
- **400**: Bad Request (invalid parameters)
- **401**: Unauthorized (missing/invalid authentication)
- **403**: Forbidden (feature flag disabled or insufficient permissions)
- **422**: Unprocessable Entity (validation error)
- **429**: Too Many Requests (rate limit exceeded)
- **500**: Internal Server Error

### Error Handling Example

```python
try:
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    result = response.json()
except requests.exceptions.HTTPError as e:
    if e.response.status_code == 401:
        print("Authentication failed - check credentials")
    elif e.response.status_code == 403:
        print("Primitive is disabled or insufficient permissions")
    elif e.response.status_code == 422:
        print(f"Validation error: {e.response.json()['detail']}")
    elif e.response.status_code == 429:
        print("Rate limit exceeded - retry after delay")
    else:
        print(f"Request failed: {e}")
except requests.exceptions.RequestException as e:
    print(f"Network error: {e}")
```

## Rate Limits

Rate limits are enforced per authentication method:

| Auth Method | Rate Limit       | Window  |
|-------------|------------------|---------|
| JWT Token   | 5000 requests    | 1 hour  |
| API Key     | 1000 requests    | 1 hour  |

**Rate Limit Headers**:
```
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4999
X-RateLimit-Reset: 1705315200
```

**Retry Logic**:
```python
import time

def call_with_retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429:
                reset_time = int(e.response.headers.get('X-RateLimit-Reset', 0))
                wait_time = max(reset_time - time.time(), 60)
                print(f"Rate limited, waiting {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise
    raise Exception("Max retries exceeded")
```

## Best Practices

### 1. Parameter Validation First

Always verify strategy parameters before running backtests or collecting evidence:

```python
# Verify parameters before expensive operations
verify_response = verify_strategy(strategy_config)
if not verify_response["data"]["valid"]:
    fix_parameters(verify_response["data"]["failed_checks"])
    return

# Proceed with backtest only if parameters valid
backtest_results = run_backtest(strategy_config)
```

### 2. Evidence Freshness

Check evidence freshness before making promotion decisions:

```python
if not evidence_result["details"]["is_fresh"]:
    print("Re-running gate checks due to stale evidence")
    new_evidence = run_fresh_gates()
```

### 3. Iterative Improvement

Use reflexion feedback in an iterative loop:

```python
for iteration in range(max_iterations):
    suggestions = get_reflexion_suggestions(strategy, metrics)
    
    # Apply high-priority suggestions
    high_priority = [s for s in suggestions if s["priority"] == "high"]
    if not high_priority:
        break
    
    strategy = apply_suggestions(strategy, high_priority)
    metrics = run_validation(strategy)
```

### 4. Evidence Aggregation

Collect multiple evidence types for robust promotion decisions:

```python
evidence_types = ["backtest", "gate_check", "validation", "production_metrics"]
classifications = []

for ev_type in evidence_types:
    result = classify_evidence(evidence_id, ev_type, data)
    classifications.append(result["classification"])

# Require all evidence types to pass
can_promote = all(c in ["valid", "contract-valid-success"] for c in classifications)
```

### 5. Async Batch Processing

Process multiple strategies in parallel:

```python
import asyncio
import aiohttp

async def verify_strategies(strategies):
    async with aiohttp.ClientSession() as session:
        tasks = [verify_strategy_async(session, s) for s in strategies]
        return await asyncio.gather(*tasks)

results = asyncio.run(verify_strategies(strategy_batch))
```

## Support and Resources

- **API Reference**: [OpenAPI Spec](http://localhost:8000/api/primitives/v1/openapi.json)
- **Health Checks**:
  - Strategy: `GET /api/primitives/v1/strategy/health`
  - Evidence: `GET /api/primitives/v1/evidence/health`
  - Reflexion: `GET /api/primitives/v1/reflexion/health`
- **Feature Flags**: Check `GET /api/v1/health` for primitive availability

---

**Document Version**: 1.0  
**Last Updated**: 2024-01-15  
**API Version**: v1
