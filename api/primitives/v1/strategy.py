"""
Strategy verification primitive endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime

from services.strategy_verification import (
    StrategyVerificationService,
    StrategyVerifyRequest,
    StrategyVerifyResponse
)
from security.auth import get_current_user_or_api_key, FeatureFlags, get_feature_flags

router = APIRouter(prefix="/strategy", tags=["Strategy Primitive"])


@router.post("/verify", response_model=Dict[str, Any])
async def verify_strategy(
    request: StrategyVerifyRequest,
    user=Depends(get_current_user_or_api_key),
    feature_flags: FeatureFlags = Depends(get_feature_flags)
):
    """
    Verify strategy configuration.
    
    Validates:
    - Strategy type validity
    - Required parameters presence
    - Parameter value ranges
    - Parameter types
    - Business logic rules
    - Risk management consistency
    """
    # Check if strategy primitive is enabled
    try:
        feature_flags.check_primitive_enabled("strategy")
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    # Verify strategy
    result = StrategyVerificationService.verify_strategy(
        strategy_id=request.strategy_id,
        strategy_type=request.strategy_type,
        parameters=request.parameters,
        context=request.context
    )
    
    # Canonical response envelope
    return {
        "data": {
            "strategy_id": result.strategy_id,
            "valid": result.valid,
            "validation_score": result.validation_score,
            "checks": [
                {
                    "check_name": check.check_name,
                    "passed": check.passed,
                    "severity": check.severity,
                    "message": check.message,
                    "actual_value": check.actual_value,
                    "expected_range": check.expected_range
                }
                for check in result.checks
            ],
            "issues": result.issues,
            "warnings": result.warnings,
            "summary": result.summary
        },
        "meta": {
            "timestamp": result.timestamp,
            "primitive": "strategy",
            "version": "v1"
        },
        "links": {
            "self": "/api/primitives/v1/strategy/verify",
            "health": "/api/primitives/v1/strategy/health",
            "docs": "/api/primitives/v1/openapi.json"
        }
    }


@router.get("/health")
async def strategy_health():
    """Health check for strategy primitive."""
    return {
        "status": "healthy",
        "primitive": "strategy",
        "version": "v1",
        "timestamp": datetime.utcnow().isoformat()
    }
