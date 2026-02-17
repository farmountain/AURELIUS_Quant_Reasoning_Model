"""
Determinism Primitive API Endpoint

Standalone determinism scoring endpoint for backtest result consistency verification.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Tuple
from schemas.primitives import create_canonical_response, create_error_response, ErrorCode
from services.determinism_scoring import (
    DeterminismScoringService,
    DeterminismScoreRequest,
    DeterminismScoreResponse
)
from security.dual_auth import get_authenticated_user
from primitives.feature_flags import FeatureFlags

router = APIRouter(prefix="/determinism", tags=["determinism"])


@router.post("/score", response_model=dict)
async def score_determinism(
    request: DeterminismScoreRequest,
    auth: Tuple = Depends(get_authenticated_user)
):
    """
    Score determinism of backtest results across multiple runs.
    
    Analyzes variance in key metrics (returns, Sharpe, drawdown, trade count)
    to detect non-deterministic behavior that could indicate bugs or data issues.
    
    **Authentication:** Requires API key (X-API-Key) or JWT token (Authorization: Bearer)
    
    **Rate Limits:**
    - API key: 1000 requests/hour
    - JWT token: 5000 requests/hour
    
    **Request:**
    - `strategy_id`: Strategy identifier
    - `runs`: List of 2+ backtest runs with identical parameters
    - `threshold`: Minimum score to pass (default: 95.0)
    
    **Response:**
    - `score`: Determinism score 0-100 (100 = perfect determinism)
    - `passed`: Whether score meets threshold
    - `confidence_interval`: Statistical confidence (0-1)
    - `p_value`: Statistical significance
    - `variance_metrics`: Variance for each metric
    - `issues`: List of detected non-deterministic behaviors
    
    **Example:**
    ```python
    import requests
    
    response = requests.post(
        "https://api.aurelius.ai/api/primitives/v1/determinism/score",
        headers={"X-API-Key": "your_api_key"},
        json={
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
    )
    
    result = response.json()
    print(f"Determinism score: {result['data']['score']}")
    print(f"Passed: {result['data']['passed']}")
    ```
    """
    # Check feature flag
    FeatureFlags.check_primitive_enabled("determinism")
    
    user_id, auth_method, rate_limit_headers = auth
    
    try:
        # Validate request
        if len(request.runs) < 2:
            return create_error_response(
                code=ErrorCode.VALIDATION_ERROR,
                message="At least 2 backtest runs required for determinism scoring",
                details={"runs_provided": len(request.runs), "runs_required": 2}
            )
        
        # Score determinism
        result = DeterminismScoringService.score_determinism(request)
        
        # Create canonical response
        response = create_canonical_response(
            data=result.model_dump(),
            links={
                "self": f"/api/primitives/v1/determinism/score",
                "docs": "https://developers.aurelius.ai/primitives/determinism",
                "strategy": f"/api/v1/strategies/{request.strategy_id}"
            }
        )
        
        return response.model_dump()
        
    except ValueError as e:
        return create_error_response(
            code=ErrorCode.VALIDATION_ERROR,
            message=str(e)
        ).model_dump()
    
    except Exception as e:
        return create_error_response(
            code=ErrorCode.INTERNAL_ERROR,
            message="Failed to score determinism",
            details={"error": str(e)}
        ).model_dump()


@router.get("/health")
async def determinism_health():
    """
    Health check for determinism primitive.
    
    Returns primitive status and configuration.
    """
    return create_canonical_response(
        data={
            "status": "healthy",
            "primitive": "determinism",
            "version": "v1",
            "enabled": FeatureFlags.is_primitive_enabled("determinism"),
            "capabilities": [
                "multi_run_comparison",
                "variance_analysis",
                "statistical_significance"
            ]
        }
    ).model_dump()
