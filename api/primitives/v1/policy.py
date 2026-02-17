"""Policy checking primitive API endpoint."""

from typing import Tuple
from fastapi import APIRouter, Depends

from services.policy_checking import (
    PolicyCheckRequest,
    PolicyCheckResponse,
    PolicyCheckingService
)
from security.auth import get_authenticated_user
from schemas.primitives import create_canonical_response
from config import FeatureFlags

router = APIRouter(prefix="/policy", tags=["policy"])


@router.post("/check", response_model=dict)
async def check_policy(
    request: PolicyCheckRequest,
    auth: Tuple = Depends(get_authenticated_user)
):
    """
    Check policy compliance against rules and constraints.
    
    This primitive validates regulatory rules, business constraints, governance
    policies, and compliance requirements.
    
    **Authentication:** API Key OR JWT token required
    
    **Rate Limits:**
    - API Key: 1000 requests/hour
    - JWT: 5000 requests/hour
    """
    # Check feature flag
    FeatureFlags.check_primitive_enabled("policy")
    
    user_id, auth_method, rate_limit_headers = auth
    
    # Check policies
    response_data = PolicyCheckingService.check_policies(
        strategy_id=request.strategy_id,
        context=request.context,
        rules=request.rules
    )
    
    # Build canonical response
    response = create_canonical_response(
        data=response_data.dict(),
        links={
            "self": f"/api/primitives/v1/policy/check",
            "docs": "/api/primitives/v1/docs#policy-checking",
            "risk": "/api/primitives/v1/risk/validate",
            "gates": "/api/primitives/v1/gates/verify"
        }
    )
    
    return response


@router.get("/health", response_model=dict)
async def policy_health():
    """Health check for policy primitive."""
    return {
        "status": "healthy",
        "primitive": "policy",
        "rule_types": ["regulatory", "business", "governance", "compliance"]
    }
