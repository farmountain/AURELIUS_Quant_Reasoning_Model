"""
Reflexion feedback primitive endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime

from services.reflexion_feedback import (
    ReflexionFeedbackService,
    ReflexionSuggestRequest,
    ReflexionSuggestResponse
)
from security.auth import get_current_user_or_api_key, FeatureFlags, get_feature_flags

router = APIRouter(prefix="/reflexion", tags=["Reflexion Primitive"])


@router.post("/suggest", response_model=Dict[str, Any])
async def suggest_improvements(
    request: ReflexionSuggestRequest,
    user=Depends(get_current_user_or_api_key),
    feature_flags: FeatureFlags = Depends(get_feature_flags)
):
    """
    Generate improvement suggestions for strategy refinement.
    
    Analyzes:
    - Iteration performance trajectory
    - User feedback
    - Current metric values
    - Strategy context
    
    Returns prioritized suggestions with:
    - Improvement score (-2.0 to +2.0)
    - Category-organized recommendations
    - Priority levels (high/medium/low)
    - Expected impact descriptions
    """
    # Check if reflexion primitive is enabled
    try:
        feature_flags.check_primitive_enabled("reflexion")
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    # Generate suggestions
    result = ReflexionFeedbackService.suggest_improvements(
        strategy_id=request.strategy_id,
        iteration_num=request.iteration_num,
        feedback=request.feedback,
        metrics=request.metrics,
        context=request.context
    )
    
    # Canonical response envelope
    return {
        "data": {
            "strategy_id": result.strategy_id,
            "iteration_num": result.iteration_num,
            "improvement_score": result.improvement_score,
            "suggestions": [
                {
                    "category": s.category,
                    "priority": s.priority,
                    "description": s.description,
                    "rationale": s.rationale,
                    "expected_impact": s.expected_impact
                }
                for s in result.suggestions
            ],
            "summary": result.summary
        },
        "meta": {
            "timestamp": result.timestamp,
            "primitive": "reflexion",
            "version": "v1"
        },
        "links": {
            "self": "/api/primitives/v1/reflexion/suggest",
            "health": "/api/primitives/v1/reflexion/health",
            "docs": "/api/primitives/v1/openapi.json"
        }
    }


@router.get("/health")
async def reflexion_health():
    """Health check for reflexion primitive."""
    return {
        "status": "healthy",
        "primitive": "reflexion",
        "version": "v1",
        "timestamp": datetime.utcnow().isoformat()
    }
