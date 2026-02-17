"""
OpenAPI specification endpoints for AURELIUS primitives.

Provides machine-readable API documentation for SDK generation and
interactive API explorer integration.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from typing import Dict, Any

router = APIRouter(prefix="/openapi", tags=["openapi"])


def generate_primitives_openapi_spec() -> Dict[str, Any]:
    """
    Generate OpenAPI 3.0 specification for AURELIUS API primitives.
    
    Returns comprehensive API documentation including:
    - All primitive endpoints with request/response schemas
    - Authentication requirements (API key, JWT)
    - Error codes and canonical response envelope
    - Rate limiting policies
    """
    spec = {
        "openapi": "3.0.0",
        "info": {
            "title": "AURELIUS Financial Reasoning Infrastructure API",
            "version": "1.0.0",
            "description": "Composable primitives for financial reasoning verification. "
                           "Integrate determinism scoring, risk validation, policy checking, "
                           "and gate verification into your quantitative workflows.",
            "contact": {
                "name": "AURELIUS API Support",
                "url": "https://developers.aurelius.ai",
                "email": "api@aurelius.ai"
            },
            "license": {
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT"
            }
        },
        "servers": [
            {
                "url": "https://api.aurelius.ai",
                "description": "Production"
            },
            {
                "url": "https://staging.api.aurelius.ai",
                "description": "Staging"
            },
            {
                "url": "http://localhost:8000",
                "description": "Local development"
            }
        ],
        "paths": {
            "/api/primitives/v1/determinism/score": {
                "post": {
                    "tags": ["determinism"],
                    "summary": "Score determinism of backtest results",
                    "description": "Analyzes variance in key metrics across multiple backtest runs to detect non-deterministic behavior. "
                                   "A score of 100 indicates perfect determinism. Scores below 95 typically indicate bugs or data issues.",
                    "operationId": "score_determinism",
                    "security": [
                        {"ApiKeyAuth": []},
                        {"BearerAuth": []}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/DeterminismScoreRequest"},
                                "example": {
                                    "strategy_id": "strat-123",
                                    "runs": [
                                        {
                                            "run_id": "run-1",
                                            "timestamp": "2026-02-16T10:00:00Z",
                                            "total_return": 0.15,
                                            "sharpe_ratio": 1.8,
                                            "max_drawdown": 0.12,
                                            "trade_count": 42,
                                            "final_portfolio_value": 115000.0,
                                            "execution_time_ms": 1250
                                        },
                                        {
                                            "run_id": "run-2",
                                            "timestamp": "2026-02-16T10:05:00Z",
                                            "total_return": 0.15,
                                            "sharpe_ratio": 1.8,
                                            "max_drawdown": 0.12,
                                            "trade_count": 42,
                                            "final_portfolio_value": 115000.0,
                                            "execution_time_ms": 1230
                                        }
                                    ],
                                    "threshold": 95.0
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Determinism scoring completed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CanonicalEnvelope"},
                                    "example": {
                                        "data": {
                                            "score": 98.5,
                                            "passed": True,
                                            "confidence_interval": 0.95,
                                            "p_value": 0.001,
                                            "variance_metrics": {
                                                "total_return": 0.0,
                                                "sharpe_ratio": 0.0,
                                                "max_drawdown": 0.0,
                                                "trade_count": 0.0
                                            },
                                            "issues": []
                                        },
                                        "meta": {
                                            "version": "v1",
                                            "timestamp": "2026-02-17T14:30:00Z",
                                            "request_id": "req-abc123"
                                        },
                                        "links": {
                                            "self": "/api/primitives/v1/determinism/score",
                                            "docs": "/api/primitives/openapi/v1.json"
                                        }
                                    }
                                }
                            },
                            "headers": {
                                "X-RateLimit-Limit": {
                                    "schema": {"type": "integer"},
                                    "description": "Request limit per hour"
                                },
                                "X-RateLimit-Remaining": {
                                    "schema": {"type": "integer"},
                                    "description": "Remaining requests in window"
                                },
                                "X-RateLimit-Reset": {
                                    "schema": {"type": "integer"},
                                    "description": "Unix timestamp when limit resets"
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid request (fewer than 2 runs, invalid threshold)",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "401": {"$ref": "#/components/responses/Unauthorized"},
                        "429": {"$ref": "#/components/responses/RateLimitExceeded"},
                        "503": {
                            "description": "Primitive disabled via feature flag",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/primitives/v1/determinism/health": {
                "get": {
                    "tags": ["determinism"],
                    "summary": "Check determinism primitive health",
                    "description": "Health check endpoint for monitoring",
                    "operationId": "determinism_health",
                    "responses": {
                        "200": {
                            "description": "Primitive is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "ok"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/primitives/v1/gates/verify": {
                "post": {
                    "tags": ["gates"],
                    "summary": "Verify strategy against gate requirements",
                    "description": "Performs gate verification checks (dev, CRV, or product) to determine promotion readiness.",
                    "operationId": "verify_gate",
                    "security": [
                        {"ApiKeyAuth": []},
                        {"BearerAuth": []}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/GateVerifyRequest"},
                                "example": {
                                    "strategy_id": "strat-123",
                                    "gate_type": "dev",
                                    "backtest_metrics": {
                                        "run_identity": "run-abc",
                                        "sharpe_ratio": 1.8,
                                        "max_drawdown": 0.12,
                                        "total_return": 0.15,
                                        "replay_pass": True
                                    },
                                    "thresholds": {
                                        "min_sharpe": 1.0,
                                        "max_drawdown": 0.20,
                                        "min_return": 0.10
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Gate verification completed",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CanonicalEnvelope"},
                                    "example": {
                                        "data": {
                                            "strategy_id": "strat-123",
                                            "gate_type": "dev",
                                            "passed": True,
                                            "gate_status": "passed",
                                            "checks": [
                                                {
                                                    "check_name": "Strategy Exists",
                                                    "passed": True,
                                                    "description": "Strategy artifact must exist",
                                                    "message": "strategy_id=strat-123",
                                                    "severity": "error"
                                                }
                                            ],
                                            "score": 100.0,
                                            "recommendations": []
                                        },
                                        "meta": {
                                            "version": "v1",
                                            "timestamp": "2026-02-17T15:00:00Z",
                                            "request_id": "req-gate-123"
                                        },
                                        "links": {
                                            "self": "/api/primitives/v1/gates/verify",
                                            "docs": "/api/primitives/openapi/v1.json"
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid gate type or missing required fields",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        },
                        "401": {"$ref": "#/components/responses/Unauthorized"},
                        "429": {"$ref": "#/components/responses/RateLimitExceeded"},
                        "503": {
                            "description": "Gates primitive disabled via feature flag",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                                }
                            }
                        }
                    }
                }
            },
            "/api/primitives/v1/gates/health": {
                "get": {
                    "tags": ["gates"],
                    "summary": "Check gates primitive health",
                    "description": "Health check endpoint for monitoring",
                    "operationId": "gates_health",
                    "responses": {
                        "200": {
                            "description": "Primitive is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "ok"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/api/primitives/v1/risk/validate": {
                "post": {
                    "tags": ["risk"],
                    "summary": "Validate risk metrics",
                    "description": "Validates Sharpe ratio, Sortino ratio, max drawdown, VaR, Calmar ratio, and volatility against configurable thresholds.",
                    "operationId": "validate_risk",
                    "security": [
                        {"ApiKeyAuth": []},
                        {"BearerAuth": []}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/RiskValidateRequest"},
                                "example": {
                                    "strategy_id": "momentum_v1",
                                    "metrics": {
                                        "sharpe_ratio": 1.5,
                                        "sortino_ratio": 1.8,
                                        "max_drawdown": 0.15,
                                        "var_95": -0.03,
                                        "var_99": -0.06,
                                        "calmar_ratio": 0.8,
                                        "volatility": 0.25
                                    },
                                    "thresholds": {
                                        "min_sharpe": 1.0,
                                        "max_drawdown": 0.20
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Risk validation completed",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CanonicalEnvelope"}
                                }
                            }
                        },
                        "401": {"$ref": "#/components/responses/Unauthorized"},
                        "429": {"$ref": "#/components/responses/RateLimitExceeded"}
                    }
                }
            },
            "/api/primitives/v1/risk/health": {
                "get": {
                    "tags": ["risk"],
                    "summary": "Check risk primitive health",
                    "operationId": "risk_health",
                    "responses": {
                        "200": {
                            "description": "Primitive is healthy"
                        }
                    }
                }
            },
            "/api/primitives/v1/policy/check": {
                "post": {
                    "tags": ["policy"],
                    "summary": "Check policy compliance",
                    "description": "Validates regulatory rules, business constraints, governance policies, and compliance requirements.",
                    "operationId": "check_policy",
                    "security": [
                        {"ApiKeyAuth": []},
                        {"BearerAuth": []}
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PolicyCheckRequest"},
                                "example": {
                                    "strategy_id": "momentum_v1",
                                    "context": {
                                        "max_drawdown": 0.15,
                                        "max_leverage": 1.5,
                                        "turnover_rate": 2.5,
                                        "lineage_complete": True,
                                        "governance_compliant": True
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Policy check completed",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CanonicalEnvelope"}
                                }
                            }
                        },
                        "401": {"$ref": "#/components/responses/Unauthorized"},
                        "429": {"$ref": "#/components/responses/RateLimitExceeded"}
                    }
                }
            },
            "/api/primitives/v1/policy/health": {
                "get": {
                    "tags": ["policy"],
                    "summary": "Check policy primitive health",
                    "operationId": "policy_health",
                    "responses": {
                        "200": {
                            "description": "Primitive is healthy"
                        }
                    }
                }
            },
            "/api/primitives/v1/strategy/verify": {
                "post": {
                    "tags": ["strategy"],
                    "summary": "Verify strategy configuration",
                    "operationId": "strategy_verify",
                    "security": [{"ApiKeyAuth": []}, {"BearerAuth": []}],
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/StrategyVerifyRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Strategy verification result",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CanonicalEnvelope"}
                                }
                            }
                        },
                        "401": {"$ref": "#/components/responses/Unauthorized"},
                        "403": {"$ref": "#/components/responses/Forbidden"},
                        "429": {"$ref": "#/components/responses/RateLimitExceeded"}
                    }
                }
            },
            "/api/primitives/v1/strategy/health": {
                "get": {
                    "tags": ["strategy"],
                    "summary": "Check strategy primitive health",
                    "operationId": "strategy_health",
                    "responses": {
                        "200": {
                            "description": "Primitive is healthy"
                        }
                    }
                }
            },
            "/api/primitives/v1/evidence/classify": {
                "post": {
                    "tags": ["evidence"],
                    "summary": "Classify evidence for promotion readiness",
                    "operationId": "evidence_classify",
                    "security": [{"ApiKeyAuth": []}, {"BearerAuth": []}],
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/EvidenceClassifyRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Evidence classification result",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CanonicalEnvelope"}
                                }
                            }
                        },
                        "401": {"$ref": "#/components/responses/Unauthorized"},
                        "403": {"$ref": "#/components/responses/Forbidden"},
                        "429": {"$ref": "#/components/responses/RateLimitExceeded"}
                    }
                }
            },
            "/api/primitives/v1/evidence/health": {
                "get": {
                    "tags": ["evidence"],
                    "summary": "Check evidence primitive health",
                    "operationId": "evidence_health",
                    "responses": {
                        "200": {
                            "description": "Primitive is healthy"
                        }
                    }
                }
            },
            "/api/primitives/v1/reflexion/suggest": {
                "post": {
                    "tags": ["reflexion"],
                    "summary": "Generate improvement suggestions for strategy refinement",
                    "operationId": "reflexion_suggest",
                    "security": [{"ApiKeyAuth": []}, {"BearerAuth": []}],
                    "requestBody": {
                        "required": true,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ReflexionSuggestRequest"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Reflexion feedback with improvement suggestions",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CanonicalEnvelope"}
                                }
                            }
                        },
                        "401": {"$ref": "#/components/responses/Unauthorized"},
                        "403": {"$ref": "#/components/responses/Forbidden"},
                        "429": {"$ref": "#/components/responses/RateLimitExceeded"}
                    }
                }
            },
            "/api/primitives/v1/reflexion/health": {
                "get": {
                    "tags": ["reflexion"],
                    "summary": "Check reflexion primitive health",
                    "operationId": "reflexion_health",
                    "responses": {
                        "200": {
                            "description": "Primitive is healthy"
                        }
                    }
                }
            },
            "/api/primitives/v1/readiness/score": {
                "post": {
                    "tags": ["readiness"],
                    "summary": "Score promotion readiness using DROPS scorecard",
                    "description": "Computes weighted readiness score from verification signals (Determinism, Risk, Policy, Ops, User dimensions).",
                    "operationId": "score_readiness",
                    "security": [{"ApiKeyAuth": []}, {"BearerAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/ReadinessScoreRequest"},
                                "example": {
                                    "strategy_id": "momentum-v2",
                                    "signals": {
                                        "run_identity_present": True,
                                        "parity_checked": True,
                                        "parity_passed": True,
                                        "validation_passed": True,
                                        "crv_available": True,
                                        "risk_metrics_complete": True,
                                        "policy_block_reasons": [],
                                        "lineage_complete": True,
                                        "startup_status": "healthy",
                                        "startup_reasons": [],
                                        "evidence_stale": False,
                                        "environment_caveat": None,
                                        "evidence_classification": "GREEN",
                                        "evidence_timestamp": "2024-01-15T10:30:00Z",
                                        "contract_mismatch": False,
                                        "maturity_label_visible": True
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Readiness score computed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/CanonicalEnvelope"},
                                    "example": {
                                        "data": {
                                            "strategy_id": "momentum-v2",
                                            "overall_score": 92.5,
                                            "color": "GREEN",
                                            "recommendation": "Strategy ready for promotion",
                                            "dimensions": {
                                                "D": 100.0,
                                                "R": 95.0,
                                                "O": 100.0,
                                                "P": 85.0,
                                                "U": 80.0
                                            },
                                            "blockers": []
                                        },
                                        "meta": {
                                            "version": "v1",
                                            "timestamp": "2024-01-15T10:30:00Z",
                                            "primitive": "readiness"
                                        },
                                        "links": {
                                            "self": "/api/primitives/v1/readiness/score"
                                        }
                                    }
                                }
                            }
                        },
                        "400": {"$ref": "#/components/responses/BadRequest"},
                        "401": {"$ref": "#/components/responses/Unauthorized"},
                        "403": {"$ref": "#/components/responses/Forbidden"},
                        "429": {"$ref": "#/components/responses/RateLimitExceeded"}
                    }
                }
            },
            "/api/primitives/v1/readiness/health": {
                "get": {
                    "tags": ["readiness"],
                    "summary": "Check readiness primitive health",
                    "operationId": "readiness_health",
                    "responses": {
                        "200": {
                            "description": "Primitive is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "healthy"},
                                            "primitive": {"type": "string", "example": "readiness"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "CanonicalEnvelope": {
                    "type": "object",
                    "description": "Standard response envelope for all primitive APIs",
                    "properties": {
                        "data": {
                            "type": "object",
                            "description": "Response payload specific to the endpoint"
                        },
                        "meta": {
                            "type": "object",
                            "properties": {
                                "version": {"type": "string", "example": "v1"},
                                "timestamp": {"type": "string", "format": "date-time"},
                                "request_id": {"type": "string", "format": "uuid"}
                            }
                        },
                        "links": {
                            "type": "object",
                            "description": "HATEOAS links to related resources",
                            "additionalProperties": {"type": "string", "format": "uri"}
                        }
                    },
                    "required": ["data", "meta"]
                },
                "ErrorResponse": {
                    "type": "object",
                    "properties": {
                        "error": {
                            "type": "object",
                            "properties": {
                                "code": {"type": "string", "example": "VALIDATION_ERROR"},
                                "message": {"type": "string"},
                                "details": {"type": "object"}
                            },
                            "required": ["code", "message"]
                        },
                        "meta": {
                            "type": "object",
                            "properties": {
                                "timestamp": {"type": "string", "format": "date-time"},
                                "request_id": {"type": "string", "format": "uuid"}
                            }
                        }
                    },
                    "required": ["error", "meta"]
                },
                "BacktestRun": {
                    "type": "object",
                    "description": "Single backtest run result",
                    "properties": {
                        "run_id": {"type": "string", "example": "run-1"},
                        "timestamp": {"type": "string", "format": "date-time", "example": "2026-02-16T10:00:00Z"},
                        "total_return": {"type": "number", "format": "float", "example": 0.15},
                        "sharpe_ratio": {"type": "number", "format": "float", "example": 1.8},
                        "max_drawdown": {"type": "number", "format": "float", "example": 0.12},
                        "trade_count": {"type": "integer", "example": 42},
                        "final_portfolio_value": {"type": "number", "format": "float", "example": 115000.0},
                        "execution_time_ms": {"type": "number", "format": "float", "example": 1250}
                    },
                    "required": ["run_id", "timestamp", "total_return", "sharpe_ratio", "max_drawdown", "trade_count", "final_portfolio_value", "execution_time_ms"]
                },
                "DeterminismScoreRequest": {
                    "type": "object",
                    "description": "Request for determinism scoring of backtest results",
                    "properties": {
                        "strategy_id": {"type": "string", "example": "strat-123"},
                        "runs": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/BacktestRun"},
                            "minItems": 2,
                            "description": "At least 2 runs required for comparison"
                        },
                        "threshold": {
                            "type": "number",
                            "format": "float",
                            "default": 95.0,
                            "minimum": 0,
                            "maximum": 100,
                            "example": 95.0,
                            "description": "Minimum score to pass (0-100)"
                        }
                    },
                    "required": ["strategy_id", "runs"]
                },
                "DeterminismScoreResponse": {
                    "type": "object",
                    "description": "Determinism scoring result",
                    "properties": {
                        "score": {
                            "type": "number",
                            "format": "float",
                            "minimum": 0,
                            "maximum": 100,
                            "example": 98.5,
                            "description": "Determinism score (0-100, 100=perfect)"
                        },
                        "passed": {"type": "boolean", "example": true, "description": "Whether score meets threshold"},
                        "confidence_interval": {"type": "number", "format": "float", "example": 0.95, "description": "Statistical confidence (0-1)"},
                        "p_value": {"type": "number", "format": "float", "example": 0.001, "description": "Statistical significance"},
                        "variance_metrics": {
                            "type": "object",
                            "description": "Variance across runs for each metric",
                            "properties": {
                                "total_return": {"type": "number", "format": "float", "example": 0.0},
                                "sharpe_ratio": {"type": "number", "format": "float", "example": 0.0},
                                "max_drawdown": {"type": "number", "format": "float", "example": 0.0},
                                "trade_count": {"type": "number", "format": "float", "example": 0.0}
                            }
                        },
                        "issues": {
                            "type": "array",
                            "items": {"type": "string"},
                            "example": [],
                            "description": "Detected non-deterministic behaviors"
                        }
                    },
                    "required": ["score", "passed", "confidence_interval", "p_value", "variance_metrics", "issues"]
                },
                "GateCheck": {
                    "type": "object",
                    "description": "Individual gate check result",
                    "properties": {
                        "check_name": {"type": "string", "example": "Strategy Exists"},
                        "passed": {"type": "boolean", "example": true},
                        "description": {"type": "string", "example": "Strategy artifact must exist"},
                        "message": {"type": "string", "example": "strategy_id=strat-123"},
                        "severity": {"type": "string", "enum": ["error", "warning", "info"], "default": "error"}
                    },
                    "required": ["check_name", "passed", "description"]
                },
                "GateVerifyRequest": {
                    "type": "object",
                    "description": "Request for gate verification",
                    "properties": {
                        "strategy_id": {"type": "string", "example": "strat-123"},
                        "gate_type": {
                            "type": "string",
                            "enum": ["dev", "crv", "product"],
                            "example": "dev",
                            "description": "Type of gate to verify"
                        },
                        "backtest_metrics": {
                            "type": "object",
                            "description": "Backtest metrics for verification",
                            "example": {
                                "run_identity": "run-abc",
                                "sharpe_ratio": 1.8,
                                "max_drawdown": 0.12,
                                "total_return": 0.15,
                                "replay_pass": true
                            }
                        },
                        "validation_metrics": {
                            "type": "object",
                            "description": "Validation metrics (for product gate)"
                        },
                        "thresholds": {
                            "type": "object",
                            "description": "Custom thresholds",
                            "properties": {
                                "min_sharpe": {"type": "number", "example": 1.0},
                                "max_drawdown": {"type": "number", "example": 0.20},
                                "min_return": {"type": "number", "example": 0.10}
                            }
                        }
                    },
                    "required": ["strategy_id", "gate_type"]
                },
                "GateVerifyResponse": {
                    "type": "object",
                    "description": "Gate verification result",
                    "properties": {
                        "strategy_id": {"type": "string", "example": "strat-123"},
                        "gate_type": {"type": "string", "example": "dev"},
                        "passed": {"type": "boolean", "example": true},
                        "gate_status": {
                            "type": "string",
                            "enum": ["passed", "failed", "blocked"],
                            "example": "passed"
                        },
                        "checks": {
                            "type": "array",
                            "items": {"$ref": "#/components/schemas/GateCheck"}
                        },
                        "score": {"type": "number", "format": "float", "example": 100.0, "description": "Overall gate score (0-100)"},
                        "readiness_payload": {"type": "object", "description": "Promotion readiness data"},
                        "recommendations": {
                            "type": "array",
                            "items": {"type": "string"},
                            "example": [],
                            "description": "Improvement recommendations"
                        }
                    },
                    "required": ["strategy_id", "gate_type", "passed", "gate_status", "checks"]
                },
                "CustomGateDefinition": {
                    "type": "object",
                    "description": "Custom gate definition for user-defined checks",
                    "properties": {
                        "gate_id": {"type": "string", "example": "custom-liquidity-gate"},
                        "name": {"type": "string", "example": "Liquidity Gate"},
                        "description": {"type": "string", "example": "Ensures strategy trades liquid assets"},
                        "checks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "check_name": {"type": "string"},
                                    "condition": {"type": "string", "description": "JSONPath expression"},
                                    "threshold": {"type": "number"},
                                    "operator": {"type": "string", "enum": [">=", "<=", "==", "!=", ">", "<"]}
                                }
                            }
                        },
                        "enabled": {"type": "boolean", "default": true}
                    },
                    "required": ["gate_id", "name", "checks"]
                },
                "RiskValidateRequest": {
                    "type": "object",
                    "description": "Request for risk validation",
                    "properties": {
                        "strategy_id": {"type": "string", "example": "momentum_v1"},
                        "metrics": {
                            "type": "object",
                            "description": "Risk metrics to validate",
                            "properties": {
                                "sharpe_ratio": {"type": "number", "format": "float"},
                                "sortino_ratio": {"type": "number", "format": "float"},
                                "max_drawdown": {"type": "number", "format": "float"},
                                "var_95": {"type": "number", "format": "float"},
                                "var_99": {"type": "number", "format": "float"},
                                "calmar_ratio": {"type": "number", "format": "float"},
                                "volatility": {"type": "number", "format": "float"}
                            }
                        },
                        "thresholds": {
                            "type": "object",
                            "description": "Custom thresholds",
                            "properties": {
                                "min_sharpe": {"type": "number", "format": "float", "default": 1.0},
                                "min_sortino": {"type": "number", "format": "float", "default": 1.2},
                                "max_drawdown": {"type": "number", "format": "float", "default": 0.20},
                                "max_var_95": {"type": "number", "format": "float", "default": -0.05},
                                "max_var_99": {"type": "number", "format": "float", "default": -0.10},
                                "min_calmar": {"type": "number", "format": "float", "default": 0.5},
                                "max_volatility": {"type": "number", "format": "float", "default": 0.30}
                            }
                        }
                    },
                    "required": ["strategy_id", "metrics"]
                },
                "RiskValidateResponse": {
                    "type": "object",
                    "description": "Risk validation result",
                    "properties": {
                        "strategy_id": {"type": "string"},
                        "passed": {"type": "boolean"},
                        "risk_score": {"type": "number", "format": "float", "description": "Overall risk score (0-100)"},
                        "checks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "check_name": {"type": "string"},
                                    "passed": {"type": "boolean"},
                                    "description": {"type": "string"},
                                    "actual_value": {"type": "number"},
                                    "threshold_value": {"type": "number"},
                                    "severity": {"type": "string", "enum": ["error", "warning", "info"]}
                                }
                            }
                        },
                        "recommendations": {"type": "array", "items": {"type": "string"}},
                        "summary": {"type": "string"}
                    },
                    "required": ["strategy_id", "passed", "risk_score", "checks"]
                },
                "PolicyCheckRequest": {
                    "type": "object",
                    "description": "Request for policy checking",
                    "properties": {
                        "strategy_id": {"type": "string", "example": "momentum_v1"},
                        "context": {
                            "type": "object",
                            "description": "Context data for policy evaluation",
                            "additionalProperties": True
                        },
                        "rules": {
                            "type": "array",
                            "description": "Custom policy rules",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "rule_id": {"type": "string"},
                                    "rule_type": {"type": "string", "enum": ["regulatory", "business", "governance", "compliance"]},
                                    "description": {"type": "string"},
                                    "severity": {"type": "string", "enum": ["error", "warning", "info"], "default": "error"}
                                }
                            }
                        }
                    },
                    "required": ["strategy_id", "context"]
                },
                "PolicyCheckResponse": {
                    "type": "object",
                    "description": "Policy compliance result",
                    "properties": {
                        "strategy_id": {"type": "string"},
                        "passed": {"type": "boolean"},
                        "compliance_score": {"type": "number", "format": "float", "description": "Overall compliance score (0-100)"},
                        "checks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "rule_id": {"type": "string"},
                                    "passed": {"type": "boolean"},
                                    "message": {"type": "string"},
                                    "severity": {"type": "string"},
                                    "recommendation": {"type": "string"}
                                }
                            }
                        },
                        "blockers": {"type": "array", "items": {"type": "string"}, "description": "Critical policy violations"},
                        "warnings": {"type": "array", "items": {"type": "string"}, "description": "Non-critical warnings"},
                        "summary": {"type": "string"}
                    },
                    "required": ["strategy_id", "passed", "compliance_score", "checks", "blockers", "warnings"]
                },
                "StrategyVerifyRequest": {
                    "type": "object",
                    "description": "Request for strategy verification",
                    "properties": {
                        "strategy_id": {"type": "string", "example": "momentum_001"},
                        "strategy_type": {"type": "string", "enum": ["momentum", "mean_reversion", "trend_following", "pairs_trading", "volatility_trading", "ml_classifier"], "example": "momentum"},
                        "parameters": {
                            "type": "object",
                            "description": "Strategy parameters to verify",
                            "example": {
                                "lookback": 20,
                                "vol_target": 0.15,
                                "position_size": 0.25,
                                "stop_loss": 0.02,
                                "take_profit": 0.05
                            }
                        },
                        "context": {"type": "object", "description": "Additional context"}
                    },
                    "required": ["strategy_id", "strategy_type", "parameters"]
                },
                "StrategyVerifyResponse": {
                    "type": "object",
                    "description": "Strategy verification result",
                    "properties": {
                        "strategy_id": {"type": "string"},
                        "valid": {"type": "boolean"},
                        "validation_score": {"type": "number", "format": "float", "description": "Validation score (0-100)"},
                        "checks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "check_name": {"type": "string"},
                                    "passed": {"type": "boolean"},
                                    "severity": {"type": "string"},
                                    "message": {"type": "string"},
                                    "actual_value": {"type": "string"},
                                    "expected_range": {"type": "string"}
                                }
                            }
                        },
                        "issues": {"type": "array", "items": {"type": "string"}},
                        "warnings": {"type": "array", "items": {"type": "string"}},
                        "summary": {"type": "string"}
                    },
                    "required": ["strategy_id", "valid", "validation_score", "checks"]
                },
                "EvidenceClassifyRequest": {
                    "type": "object",
                    "description": "Request for evidence classification",
                    "properties": {
                        "evidence_id": {"type": "string", "example": "evidence_001"},
                        "evidence_type": {"type": "string", "enum": ["backtest", "validation", "gate_check", "acceptance_test", "production_metrics", "custom"], "example": "gate_check"},
                        "data": {
                            "type": "object",
                            "description": "Evidence data to classify",
                            "example": {
                                "dev_status": 200,
                                "crv_status": 200,
                                "product_status": 200,
                                "environment": "staging"
                            }
                        },
                        "timestamp": {"type": "string", "format": "date-time", "example": "2026-02-17T10:00:00Z"},
                        "max_age_hours": {"type": "integer", "minimum": 1, "maximum": 168, "default": 24}
                    },
                    "required": ["evidence_id", "evidence_type", "data"]
                },
                "EvidenceClassifyResponse": {
                    "type": "object",
                    "description": "Evidence classification result",
                    "properties": {
                        "evidence_id": {"type": "string"},
                        "classification": {"type": "string", "enum": ["contract-valid-success", "contract-valid-failure", "contract-invalid-failure", "mixed", "stale", "incomplete", "valid"]},
                        "confidence": {"type": "number", "format": "float", "minimum": 0, "maximum": 1},
                        "details": {
                            "type": "object",
                            "properties": {
                                "is_fresh": {"type": "boolean"},
                                "age_hours": {"type": "number", "format": "float"},
                                "completeness_score": {"type": "number", "format": "float"},
                                "quality_indicators": {"type": "object"},
                                "missing_fields": {"type": "array", "items": {"type": "string"}},
                                "warnings": {"type": "array", "items": {"type": "string"}}
                            }
                        },
                        "summary": {"type": "string"},
                        "recommendations": {"type": "array", "items": {"type": "string"}}
                    },
                    "required": ["evidence_id", "classification", "confidence", "details"]
                },
                "ReflexionSuggestRequest": {
                    "type": "object",
                    "description": "Request for reflexion feedback suggestions",
                    "properties": {
                        "strategy_id": {"type": "string", "example": "momentum_001"},
                        "iteration_num": {"type": "integer", "minimum": 1, "example": 2},
                        "feedback": {"type": "string", "example": "Strategy underperforms in high volatility regimes"},
                        "metrics": {
                            "type": "object",
                            "description": "Current strategy metrics",
                            "example": {
                                "sharpe_ratio": 1.2,
                                "max_drawdown": 0.18,
                                "win_rate": 0.55
                            }
                        },
                        "context": {"type": "object", "description": "Additional context"}
                    },
                    "required": ["strategy_id", "iteration_num"]
                },
                "ReflexionSuggestResponse": {
                    "type": "object",
                    "description": "Reflexion feedback result",
                    "properties": {
                        "strategy_id": {"type": "string"},
                        "iteration_num": {"type": "integer"},
                        "improvement_score": {"type": "number", "format": "float", "minimum": -2.0, "maximum": 2.0, "description": "Improvement score (-2.0 to +2.0)"},
                        "suggestions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "category": {"type": "string", "enum": ["parameter", "logic", "risk_management", "timing"]},
                                    "priority": {"type": "string", "enum": ["high", "medium", "low"]},
                                    "description": {"type": "string"},
                                    "rationale": {"type": "string"},
                                    "expected_impact": {"type": "string"}
                                }
                            }
                        },
                        "summary": {"type": "string"}
                    },
                    "required": ["strategy_id", "iteration_num", "improvement_score", "suggestions", "summary"]
                },
                "ReadinessScoreRequest": {
                    "type": "object",
                    "description": "Request for promotion readiness scoring",
                    "properties": {
                        "strategy_id": {"type": "string", "description": "Strategy identifier"},
                        "signals": {
                            "type": "object",
                            "description": "Readiness signals from various verification checks",
                            "properties": {
                                "run_identity_present": {"type": "boolean"},
                                "parity_checked": {"type": "boolean"},
                                "parity_passed": {"type": "boolean"},
                                "validation_passed": {"type": "boolean"},
                                "crv_available": {"type": "boolean"},
                                "risk_metrics_complete": {"type": "boolean"},
                                "policy_block_reasons": {"type": "array", "items": {"type": "string"}},
                                "lineage_complete": {"type": "boolean"},
                                "startup_status": {"type": "string", "enum": ["healthy", "degraded", "unavailable"]},
                                "startup_reasons": {"type": "array", "items": {"type": "string"}},
                                "evidence_stale": {"type": "boolean"},
                                "environment_caveat": {"type": "string", "nullable": True},
                                "evidence_classification": {"type": "string", "nullable": True},
                                "evidence_timestamp": {"type": "string", "format": "date-time", "nullable": True},
                                "contract_mismatch": {"type": "boolean"},
                                "maturity_label_visible": {"type": "boolean"}
                            },
                            "required": ["run_identity_present", "parity_checked", "parity_passed", "validation_passed", "crv_available", "risk_metrics_complete", "policy_block_reasons", "lineage_complete", "startup_status", "startup_reasons", "evidence_stale", "contract_mismatch", "maturity_label_visible"]
                        }
                    },
                    "required": ["strategy_id", "signals"]
                },
                "ReadinessScoreResponse": {
                    "type": "object",
                    "description": "Promotion readiness scoring result",
                    "properties": {
                        "strategy_id": {"type": "string"},
                        "overall_score": {"type": "number", "format": "float", "minimum": 0, "maximum": 100, "description": "Weighted DROPS score (0-100)"},
                        "color": {"type": "string", "enum": ["GREEN", "AMBER", "RED"], "description": "Traffic light band"},
                        "recommendation": {"type": "string", "description": "Human-readable promotion decision"},
                        "dimensions": {
                            "type": "object",
                            "description": "DROPS dimension scores",
                            "properties": {
                                "D": {"type": "number", "format": "float", "description": "Determinism score"},
                                "R": {"type": "number", "format": "float", "description": "Risk score"},
                                "O": {"type": "number", "format": "float", "description": "Ops score"},
                                "P": {"type": "number", "format": "float", "description": "Policy score"},
                                "U": {"type": "number", "format": "float", "description": "User/UI score"}
                            },
                            "required": ["D", "R", "O", "P", "U"]
                        },
                        "blockers": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Hard blockers preventing promotion"
                        }
                    },
                    "required": ["strategy_id", "overall_score", "color", "recommendation", "dimensions", "blockers"]
                }
            },
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-API-Key",
                    "description": "API key for external developers (1000 requests/hour)"
                },
                "BearerAuth": {
                    "type": "http",
                    "scheme": "bearer",
                    "bearerFormat": "JWT",
                    "description": "JWT token for authenticated users (5000 requests/hour)"
                }
            },
            "responses": {
                "Unauthorized": {
                    "description": "Authentication credentials missing or invalid",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    }
                },
                "Forbidden": {
                    "description": "Insufficient permissions for requested operation",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    }
                },
                "NotFound": {
                    "description": "Resource not found",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    }
                },
                "RateLimitExceeded": {
                    "description": "Rate limit exceeded",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    },
                    "headers": {
                        "X-RateLimit-Limit": {
                            "schema": {"type": "integer"},
                            "description": "Total request limit per hour"
                        },
                        "X-RateLimit-Remaining": {
                            "schema": {"type": "integer"},
                            "description": "Remaining requests in current window"
                        },
                        "X-RateLimit-Reset": {
                            "schema": {"type": "integer"},
                            "description": "Unix timestamp when limit resets"
                        }
                    }
                }
            }
        },
        "tags": [
            {
                "name": "determinism",
                "description": "Determinism scoring for backtest result consistency"
            },
            {
                "name": "risk",
                "description": "Risk validation for portfolio metrics"
            },
            {
                "name": "policy",
                "description": "Policy compliance checking"
            },
            {
                "name": "strategy",
                "description": "Strategy verification and validation"
            },
            {
                "name": "evidence",
                "description": "Acceptance evidence classification"
            },
            {
                "name": "gates",
                "description": "Gate verification and certification registry"
            },
            {
                "name": "reflexion",
                "description": "Reflexion feedback for strategy improvement"
            },
            {
                "name": "orchestrator",
                "description": "Multi-primitive workflow orchestration"
            },
            {
                "name": "readiness",
                "description": "Promotion readiness scorecard"
            }
        ]
    }
    
    return spec


@router.get("/primitives/v1.json", response_class=JSONResponse)
async def get_primitives_openapi_spec():
    """
    Get OpenAPI 3.0 specification for AURELIUS API primitives.
    
    This endpoint provides a machine-readable API specification that can be used for:
    - SDK code generation (openapi-generator, swagger-codegen)
    - Interactive API documentation (Swagger UI, Redoc)
    - Contract testing (Dredd, Schemathesis)
    - API client tools (Postman, Insomnia)
    
    The specification follows OpenAPI 3.0 standard and includes all primitive
    endpoints with complete request/response schemas, authentication requirements,
    and error codes.
    """
    spec = generate_primitives_openapi_spec()
    return JSONResponse(content=spec)


@router.get("/primitives/v1.yaml")
async def get_primitives_openapi_spec_yaml():
    """
    Get OpenAPI 3.0 specification in YAML format.
    
    Same as JSON endpoint but returns YAML for better human readability.
    """
    import yaml
    spec = generate_primitives_openapi_spec()
    yaml_content = yaml.dump(spec, default_flow_style=False, sort_keys=False)
    return JSONResponse(content=yaml_content, media_type="application/x-yaml")
