"""Risk validation primitive API endpoint."""

from typing import Tuple
from fastapi import APIRouter, Depends

from services.risk_validation import (
    RiskValidateRequest,
    RiskValidateResponse,
    RiskValidationService
)
from security.auth import get_authenticated_user
from schemas.primitives import create_canonical_response
from config import FeatureFlags

router = APIRouter(prefix="/risk", tags=["risk"])


@router.post("/validate", response_model=dict)
async def validate_risk(
    request: RiskValidateRequest,
    auth: Tuple = Depends(get_authenticated_user)
):
    """
    Validate risk metrics against thresholds.
    
    This primitive checks Sharpe ratio, Sortino ratio, max drawdown, VaR,
    Calmar ratio, and volatility against configurable thresholds.
    
    **Authentication:** API Key OR JWT token required
    
    **Rate Limits:**
    - API Key: 1000 requests/hour
    - JWT: 5000 requests/hour
    """
    # Check feature flag
    FeatureFlags.check_primitive_enabled("risk")
    
    user_id, auth_method, rate_limit_headers = auth
    
    # Validate risk metrics
    response_data = RiskValidationService.validate_risk_metrics(
        strategy_id=request.strategy_id,
        metrics=request.metrics,
        thresholds=request.thresholds
    )
    
    # Build canonical response
    response = create_canonical_response(
        data=response_data.dict(),
        links={
            "self": f"/api/primitives/v1/risk/validate",
            "docs": "/api/primitives/v1/docs#risk-validation",
            "policy": "/api/primitives/v1/policy/check"
        }
    )
    
    return response


@router.get("/health", response_model=dict)
async def risk_health():
    """Health check for risk primitive."""
    return {
        "status": "healthy",
        "primitive": "risk",
        "checks": ["sharpe", "sortino", "drawdown", "var", "calmar", "volatility"]
    }
