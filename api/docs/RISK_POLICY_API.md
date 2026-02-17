# Risk and Policy Primitives API Documentation

This document provides comprehensive documentation for the Risk and Policy primitives in the AURELIUS API.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Risk Validation Primitive](#risk-validation-primitive)
- [Policy Checking Primitive](#policy-checking-primitive)
- [Integration Examples](#integration-examples)
- [Error Handling](#error-handling)

## Overview

The Risk and Policy primitives provide standalone endpoints for validating financial risk metrics and checking policy compliance. These primitives are designed to be composable building blocks for quant workflows.

**Base URL**: `https://api.aurelius.ai/api/primitives/v1/`

**Features**:
- Dual authentication (API key or JWT token)
- Canonical response envelope structure
- Feature flag controlled rollout
- Rate limiting (1000 req/hr for API keys, 5000 req/hr for JWT)
- HATEOAS links for API navigation

## Authentication

All primitive endpoints require authentication using either:

1. **API Key** (Header): `X-API-Key: your_api_key_here`
2. **JWT Token** (Header): `Authorization: Bearer your_jwt_token_here`

To obtain API keys or JWT tokens, see the [Authentication Guide](../security/README.md).

## Risk Validation Primitive

### POST `/api/primitives/v1/risk/validate`

Validates financial risk metrics against configurable thresholds.

**Validated Metrics**:
- Sharpe Ratio (≥ threshold)
- Sortino Ratio (≥ threshold)
- Maximum Drawdown (≤ threshold)
- Value at Risk 95% (≥ threshold, negative values)
- Value at Risk 99% (≥ threshold, negative values)
- Calmar Ratio (≥ threshold)
- Volatility (≤ threshold)

#### Request Schema

```json
{
  "metrics": {
    "sharpe_ratio": 1.5,
    "sortino_ratio": 1.8,
    "max_drawdown": 0.15,
    "var_95": -0.03,
    "var_99": -0.07,
    "calmar_ratio": 0.8,
    "volatility": 0.25
  },
  "thresholds": {
    "min_sharpe": 1.0,
    "min_sortino": 1.2,
    "max_drawdown": 0.20,
    "max_var_95": -0.05,
    "max_var_99": -0.10,
    "min_calmar": 0.5,
    "max_volatility": 0.30
  },
  "context": {
    "strategy_id": "momentum_001",
    "backtest_period": "2023-01-01_to_2023-12-31"
  }
}
```

**Field Descriptions**:
- `metrics`: Object containing actual risk metric values
- `thresholds`: Object containing threshold values for validation (optional, uses defaults if omitted)
- `context`: Optional metadata for tracking and audit purposes

#### Response Schema

```json
{
  "data": {
    "overall_pass": true,
    "risk_score": 100.0,
    "checks": [
      {
        "metric": "sharpe_ratio",
        "passed": true,
        "actual": 1.5,
        "threshold": 1.0,
        "severity": "error",
        "message": "Sharpe ratio 1.5 meets minimum threshold 1.0"
      }
    ],
    "summary": "7/7 risk checks passed"
  },
  "meta": {
    "timestamp": "2026-02-17T10:30:00Z",
    "primitive": "risk",
    "version": "v1"
  },
  "links": {
    "self": "/api/primitives/v1/risk/validate",
    "health": "/api/primitives/v1/risk/health",
    "docs": "/api/primitives/v1/openapi.json"
  }
}
```

**Field Descriptions**:
- `overall_pass`: Boolean indicating if all checks passed
- `risk_score`: Percentage score (0-100) = (passed checks / total checks) × 100
- `checks`: Array of individual check results with details
- `severity`: "error" (failed) or "info" (passed)

#### Default Thresholds

| Metric | Default Threshold | Direction |
|--------|------------------|-----------|
| Sharpe Ratio | 1.0 | ≥ |
| Sortino Ratio | 1.2 | ≥ |
| Max Drawdown | 0.20 (20%) | ≤ |
| VaR 95% | -0.05 (-5%) | ≥ |
| VaR 99% | -0.10 (-10%) | ≥ |
| Calmar Ratio | 0.5 | ≥ |
| Volatility | 0.30 (30%) | ≤ |

### GET `/api/primitives/v1/risk/health`

Health check endpoint for the risk primitive.

#### Response

```json
{
  "status": "healthy",
  "primitive": "risk",
  "version": "v1",
  "timestamp": "2026-02-17T10:30:00Z"
}
```

## Policy Checking Primitive

### POST `/api/primitives/v1/policy/check`

Checks strategy policies against regulatory and business rules.

**Default Rules**:
- `max_drawdown_regulatory`: Maximum allowed drawdown (regulatory)
- `max_leverage_regulatory`: Maximum leverage ratio (regulatory)
- `lineage_completeness`: Data lineage completeness check
- `governance_compliance`: Governance approval check
- `turnover_constraint`: Portfolio turnover limit (business)

#### Request Schema

```json
{
  "policies": [
    {
      "rule_id": "max_drawdown_regulatory",
      "threshold": 0.25,
      "severity": "blocker"
    },
    {
      "rule_id": "max_leverage_regulatory",
      "threshold": 2.0,
      "severity": "blocker"
    },
    {
      "rule_id": "lineage_completeness",
      "threshold": 1.0,
      "severity": "warning"
    }
  ],
  "context": {
    "max_drawdown": 0.18,
    "leverage": 1.5,
    "lineage_complete": true,
    "governance_approved": true,
    "turnover": 3.2,
    "strategy_id": "momentum_001"
  }
}
```

**Field Descriptions**:
- `policies`: Array of policy rules to check
  - `rule_id`: Identifier for the rule
  - `threshold`: Numeric threshold value
  - `severity`: "blocker" (blocks compliance) or "warning" (advisory only)
- `context`: Object containing data for rule evaluation

#### Response Schema

```json
{
  "data": {
    "compliant": true,
    "compliance_score": 100.0,
    "blockers": [],
    "warnings": [],
    "summary": "3/3 policy checks passed"
  },
  "meta": {
    "timestamp": "2026-02-17T10:30:00Z",
    "primitive": "policy",
    "version": "v1"
  },
  "links": {
    "self": "/api/primitives/v1/policy/check",
    "health": "/api/primitives/v1/policy/health",
    "docs": "/api/primitives/v1/openapi.json"
  }
}
```

**Field Descriptions**:
- `compliant`: Boolean indicating overall compliance (false if any blockers)
- `compliance_score`: Percentage score (0-100) = (passed checks / total checks) × 100
- `blockers`: Array of failed checks with severity="blocker"
- `warnings`: Array of failed checks with severity="warning"

**Blocker Example**:
```json
{
  "rule_id": "max_drawdown_regulatory",
  "passed": false,
  "severity": "blocker",
  "message": "Max drawdown 0.30 exceeds regulatory limit 0.25",
  "actual": 0.30,
  "threshold": 0.25
}
```

### GET `/api/primitives/v1/policy/health`

Health check endpoint for the policy primitive.

#### Response

```json
{
  "status": "healthy",
  "primitive": "policy",
  "version": "v1",
  "timestamp": "2026-02-17T10:30:00Z"
}
```

## Integration Examples

### Python SDK

```python
from aurelius import Client

# Initialize client with API key
client = Client(api_key="your_api_key_here")

# Validate risk metrics
risk_result = client.primitives.risk.validate(
    metrics={
        "sharpe_ratio": 1.5,
        "sortino_ratio": 1.8,
        "max_drawdown": 0.15,
        "var_95": -0.03,
        "var_99": -0.07,
        "calmar_ratio": 0.8,
        "volatility": 0.25
    },
    thresholds={
        "min_sharpe": 1.0,
        "min_sortino": 1.2,
        "max_drawdown": 0.20,
        "max_var_95": -0.05,
        "max_var_99": -0.10,
        "min_calmar": 0.5,
        "max_volatility": 0.30
    },
    context={
        "strategy_id": "momentum_001",
        "backtest_period": "2023-01-01_to_2023-12-31"
    }
)

if risk_result.data.overall_pass:
    print(f"✓ Risk validation passed (score: {risk_result.data.risk_score})")
else:
    print(f"✗ Risk validation failed")
    for check in risk_result.data.checks:
        if not check.passed:
            print(f"  - {check.message}")

# Check policies
policy_result = client.primitives.policy.check(
    policies=[
        {"rule_id": "max_drawdown_regulatory", "threshold": 0.25, "severity": "blocker"},
        {"rule_id": "max_leverage_regulatory", "threshold": 2.0, "severity": "blocker"},
        {"rule_id": "lineage_completeness", "threshold": 1.0, "severity": "warning"}
    ],
    context={
        "max_drawdown": 0.18,
        "leverage": 1.5,
        "lineage_complete": True,
        "governance_approved": True,
        "turnover": 3.2,
        "strategy_id": "momentum_001"
    }
)

if policy_result.data.compliant:
    print(f"✓ Policy check passed (score: {policy_result.data.compliance_score})")
else:
    print(f"✗ Policy check failed")
    for blocker in policy_result.data.blockers:
        print(f"  BLOCKER: {blocker.message}")
    for warning in policy_result.data.warnings:
        print(f"  WARNING: {warning.message}")
```

### cURL

**Risk Validation**:
```bash
curl -X POST https://api.aurelius.ai/api/primitives/v1/risk/validate \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "metrics": {
      "sharpe_ratio": 1.5,
      "sortino_ratio": 1.8,
      "max_drawdown": 0.15,
      "var_95": -0.03,
      "var_99": -0.07,
      "calmar_ratio": 0.8,
      "volatility": 0.25
    },
    "thresholds": {
      "min_sharpe": 1.0,
      "min_sortino": 1.2,
      "max_drawdown": 0.20,
      "max_var_95": -0.05,
      "max_var_99": -0.10,
      "min_calmar": 0.5,
      "max_volatility": 0.30
    },
    "context": {
      "strategy_id": "momentum_001",
      "backtest_period": "2023-01-01_to_2023-12-31"
    }
  }'
```

**Policy Checking**:
```bash
curl -X POST https://api.aurelius.ai/api/primitives/v1/policy/check \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "policies": [
      {"rule_id": "max_drawdown_regulatory", "threshold": 0.25, "severity": "blocker"},
      {"rule_id": "max_leverage_regulatory", "threshold": 2.0, "severity": "blocker"},
      {"rule_id": "lineage_completeness", "threshold": 1.0, "severity": "warning"}
    ],
    "context": {
      "max_drawdown": 0.18,
      "leverage": 1.5,
      "lineage_complete": true,
      "governance_approved": true,
      "turnover": 3.2,
      "strategy_id": "momentum_001"
    }
  }'
```

### JavaScript/TypeScript

```typescript
import { AureliusClient } from '@aurelius/sdk';

// Initialize client
const client = new AureliusClient({
  apiKey: 'your_api_key_here'
});

// Validate risk metrics
const riskResult = await client.primitives.risk.validate({
  metrics: {
    sharpe_ratio: 1.5,
    sortino_ratio: 1.8,
    max_drawdown: 0.15,
    var_95: -0.03,
    var_99: -0.07,
    calmar_ratio: 0.8,
    volatility: 0.25
  },
  thresholds: {
    min_sharpe: 1.0,
    min_sortino: 1.2,
    max_drawdown: 0.20,
    max_var_95: -0.05,
    max_var_99: -0.10,
    min_calmar: 0.5,
    max_volatility: 0.30
  },
  context: {
    strategy_id: 'momentum_001',
    backtest_period: '2023-01-01_to_2023-12-31'
  }
});

console.log(`Risk Score: ${riskResult.data.risk_score}`);

// Check policies
const policyResult = await client.primitives.policy.check({
  policies: [
    { rule_id: 'max_drawdown_regulatory', threshold: 0.25, severity: 'blocker' },
    { rule_id: 'max_leverage_regulatory', threshold: 2.0, severity: 'blocker' }
  ],
  context: {
    max_drawdown: 0.18,
    leverage: 1.5,
    strategy_id: 'momentum_001'
  }
});

console.log(`Compliant: ${policyResult.data.compliant}`);
```

### Combined Workflow Example

Here's a complete workflow combining risk and policy primitives:

```python
from aurelius import Client

def validate_strategy(client, strategy_metrics):
    """
    Complete validation workflow for a trading strategy.
    """
    # Step 1: Validate risk metrics
    risk_result = client.primitives.risk.validate(
        metrics=strategy_metrics["risk_metrics"],
        thresholds=strategy_metrics["risk_thresholds"],
        context={"strategy_id": strategy_metrics["strategy_id"]}
    )
    
    if not risk_result.data.overall_pass:
        return {
            "approved": False,
            "reason": "Risk validation failed",
            "details": risk_result.data.checks
        }
    
    # Step 2: Check policy compliance
    policy_result = client.primitives.policy.check(
        policies=strategy_metrics["policies"],
        context=strategy_metrics["policy_context"]
    )
    
    if not policy_result.data.compliant:
        return {
            "approved": False,
            "reason": "Policy compliance failed",
            "blockers": policy_result.data.blockers
        }
    
    # Both checks passed
    return {
        "approved": True,
        "risk_score": risk_result.data.risk_score,
        "compliance_score": policy_result.data.compliance_score
    }

# Usage
client = Client(api_key="your_api_key_here")

strategy = {
    "strategy_id": "momentum_001",
    "risk_metrics": {
        "sharpe_ratio": 1.5,
        "sortino_ratio": 1.8,
        "max_drawdown": 0.15
    },
    "risk_thresholds": {
        "min_sharpe": 1.0,
        "min_sortino": 1.2,
        "max_drawdown": 0.20
    },
    "policies": [
        {"rule_id": "max_drawdown_regulatory", "threshold": 0.25, "severity": "blocker"}
    ],
    "policy_context": {
        "max_drawdown": 0.15,
        "leverage": 1.5
    }
}

result = validate_strategy(client, strategy)
print(result)
```

## Error Handling

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request succeeded |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Primitive disabled via feature flag |
| 422 | Unprocessable Entity | Invalid request payload |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Response Format

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request payload",
    "details": [
      {
        "field": "metrics.sharpe_ratio",
        "message": "Field required"
      }
    ]
  },
  "meta": {
    "timestamp": "2026-02-17T10:30:00Z",
    "request_id": "req_abc123"
  }
}
```

### Common Error Scenarios

**Authentication Failed**:
```json
{
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid API key or JWT token"
  }
}
```

**Feature Flag Disabled**:
```json
{
  "error": {
    "code": "FEATURE_DISABLED",
    "message": "Risk primitive is disabled. Contact support for access."
  }
}
```

**Rate Limit Exceeded**:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit of 1000 requests per hour exceeded",
    "retry_after": 3600
  }
}
```

### Best Practices

1. **Always check `overall_pass` / `compliant` flags** before proceeding with strategy deployment
2. **Handle both blockers and warnings** - warnings don't block but should be reviewed
3. **Use context fields** for audit trails and debugging
4. **Implement retry logic** with exponential backoff for transient errors
5. **Cache validation results** when appropriate to reduce API calls
6. **Monitor rate limits** and implement client-side throttling

## Rate Limits

| Authentication Type | Rate Limit |
|--------------------|------------|
| API Key | 1000 requests/hour |
| JWT Token | 5000 requests/hour |

Rate limits are applied per user/API key. When exceeded, the API returns 429 status code with `Retry-After` header.

## Support

For questions or issues:
- Documentation: https://developers.aurelius.ai
- Support: support@aurelius.ai
- GitHub: https://github.com/aurelius/api-issues

## Changelog

**v1.0.0** (2026-02-17)
- Initial release of Risk and Policy primitives
- Support for 7 risk metrics validation
- Support for 5 default policy rules
- Dual authentication (API key + JWT)
- Canonical response envelope
- Feature flag controlled rollout
