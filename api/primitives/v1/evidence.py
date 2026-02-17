"""
Evidence classification primitive endpoint.
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from datetime import datetime

from services.evidence_classification import (
    EvidenceClassificationService,
    EvidenceClassifyRequest,
    EvidenceClassifyResponse
)
from security.auth import get_current_user_or_api_key, FeatureFlags, get_feature_flags

router = APIRouter(prefix="/evidence", tags=["Evidence Primitive"])


@router.post("/classify", response_model=Dict[str, Any])
async def classify_evidence(
    request: EvidenceClassifyRequest,
    user=Depends(get_current_user_or_api_key),
    feature_flags: FeatureFlags = Depends(get_feature_flags)
):
    """
    Classify evidence for promotion readiness.
    
    Classifies evidence based on:
    - Evidence type (backtest, validation, gate_check, etc.)
    - Freshness (age vs max_age_hours)
    - Completeness (required fields present)
    - Quality indicators (thresholds, status codes)
    
    Returns classification:
    - contract-valid-success: All checks passed
    - contract-valid-failure: Some checks failed (expected)
    - contract-invalid-failure: Critical/unexpected failures
    - mixed: Inconsistent results
    - stale: Evidence too old
    - incomplete: Missing required data
    """
    # Check if evidence primitive is enabled
    try:
        feature_flags.check_primitive_enabled("evidence")
    except Exception as e:
        raise HTTPException(status_code=403, detail=str(e))
    
    # Classify evidence
    result = EvidenceClassificationService.classify_evidence(
        evidence_id=request.evidence_id,
        evidence_type=request.evidence_type,
        data=request.data,
        timestamp=request.timestamp,
        max_age_hours=request.max_age_hours
    )
    
    # Canonical response envelope
    return {
        "data": {
            "evidence_id": result.evidence_id,
            "classification": result.classification,
            "confidence": result.confidence,
            "details": {
                "is_fresh": result.details.is_fresh,
                "age_hours": result.details.age_hours,
                "completeness_score": result.details.completeness_score,
                "quality_indicators": result.details.quality_indicators,
                "missing_fields": result.details.missing_fields,
                "warnings": result.details.warnings
            },
            "summary": result.summary,
            "recommendations": result.recommendations
        },
        "meta": {
            "timestamp": result.timestamp,
            "primitive": "evidence",
            "version": "v1"
        },
        "links": {
            "self": "/api/primitives/v1/evidence/classify",
            "health": "/api/primitives/v1/evidence/health",
            "docs": "/api/primitives/v1/openapi.json"
        }
    }


@router.get("/health")
async def evidence_health():
    """Health check for evidence primitive."""
    return {
        "status": "healthy",
        "primitive": "evidence",
        "version": "v1",
        "timestamp": datetime.utcnow().isoformat()
    }
