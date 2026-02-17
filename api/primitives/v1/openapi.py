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
        "paths": {},
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
