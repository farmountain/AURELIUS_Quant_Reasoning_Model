"""
Canonical response envelope schemas for AURELIUS API primitives.

All primitive endpoints use a standardized response format:
- data: Endpoint-specific payload
- meta: Request metadata (version, timestamp, request_id)
- links: HATEOAS links to related resources

This ensures consistent client experience across all primitives.
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime
from uuid import UUID, uuid4


class ResponseMeta(BaseModel):
    """
    Metadata included in all primitive API responses.
    
    Provides request tracing, versioning, and timing information
    for debugging and observability.
    """
    version: str = Field(default="v1", description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response generation timestamp")
    request_id: UUID = Field(default_factory=uuid4, description="Unique request identifier for tracing")
    
    class Config:
        json_schema_extra = {
            "example": {
                "version": "v1",
                "timestamp": "2026-02-16T10:30:00Z",
                "request_id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class CanonicalEnvelope(BaseModel):
    """
    Standard response envelope for all AURELIUS API primitives.
    
    Wraps endpoint-specific data with metadata and HATEOAS links.
    Clients can rely on this consistent structure across all primitives.
    
    Example:
        {
            "data": {"score": 95, "components": {...}},
            "meta": {"version": "v1", "timestamp": "...", "request_id": "..."},
            "links": {"self": "/api/primitives/v1/readiness/score", "docs": "https://developers.aurelius.ai"}
        }
    """
    data: Any = Field(..., description="Endpoint-specific response payload")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Request metadata")
    links: Optional[Dict[str, str]] = Field(default=None, description="HATEOAS links to related resources")
    
    class Config:
        json_schema_extra = {
            "example": {
                "data": {
                    "score": 92,
                    "band": "GREEN",
                    "components": {"determinism": 95, "risk": 90}
                },
                "meta": {
                    "version": "v1",
                    "timestamp": "2026-02-16T10:30:00Z",
                    "request_id": "550e8400-e29b-41d4-a716-446655440000"
                },
                "links": {
                    "self": "/api/primitives/v1/readiness/score",
                    "docs": "https://developers.aurelius.ai/primitives/readiness"
                }
            }
        }


class ErrorDetail(BaseModel):
    """
    Detailed error information for validation failures.
    """
    field: Optional[str] = Field(None, description="Field that failed validation")
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code for programmatic handling")
    
    class Config:
        json_schema_extra = {
            "example": {
                "field": "backtest_results.sharpe_ratio",
                "message": "Sharpe ratio must be between -10 and 10",
                "code": "VALUE_OUT_OF_RANGE"
            }
        }


class ErrorResponse(BaseModel):
    """
    Standardized error response for all primitive APIs.
    
    Provides machine-readable error codes and human-readable messages
    for debugging and error handling in client applications.
    """
    error: Dict[str, Any] = Field(..., description="Error information")
    meta: ResponseMeta = Field(default_factory=ResponseMeta, description="Request metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": [
                        {
                            "field": "strategy_id",
                            "message": "Strategy ID must be a valid UUID",
                            "code": "INVALID_UUID"
                        }
                    ]
                },
                "meta": {
                    "version": "v1",
                    "timestamp": "2026-02-16T10:30:00Z",
                    "request_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            }
        }


# Common error codes used across primitives
class ErrorCode:
    """Standard error codes for primitive APIs."""
    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    PERMISSION_DENIED = "PERMISSION_DENIED"
    RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    TIMEOUT_ERROR = "TIMEOUT_ERROR"
    DEPENDENCY_ERROR = "DEPENDENCY_ERROR"


def create_canonical_response(
    data: Any,
    links: Optional[Dict[str, str]] = None,
    version: str = "v1"
) -> CanonicalEnvelope:
    """
    Create a canonical response envelope.
    
    Args:
        data: Endpoint-specific response payload
        links: Optional HATEOAS links to related resources
        version: API version (default: v1)
        
    Returns:
        CanonicalEnvelope with data, meta, and optional links
    """
    return CanonicalEnvelope(
        data=data,
        meta=ResponseMeta(version=version),
        links=links
    )


def create_error_response(
    code: str,
    message: str,
    details: Optional[Any] = None
) -> ErrorResponse:
    """
    Create a standardized error response.
    
    Args:
        code: Machine-readable error code (use ErrorCode constants)
        message: Human-readable error message
        details: Optional additional error details
        
    Returns:
        ErrorResponse with error info and metadata
    """
    error_data = {
        "code": code,
        "message": message
    }
    if details is not None:
        error_data["details"] = details
        
    return ErrorResponse(
        error=error_data,
        meta=ResponseMeta()
    )
