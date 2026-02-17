"""
Evidence classification service for primitive API.
"""
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from enum import Enum


class EvidenceType(str, Enum):
    """Types of evidence."""
    BACKTEST = "backtest"
    VALIDATION = "validation"
    GATE_CHECK = "gate_check"
    ACCEPTANCE_TEST = "acceptance_test"
    PRODUCTION_METRICS = "production_metrics"
    CUSTOM = "custom"


class EvidenceClassification(str, Enum):
    """Evidence classification categories."""
    CONTRACT_VALID_SUCCESS = "contract-valid-success"
    CONTRACT_VALID_FAILURE = "contract-valid-failure"
    CONTRACT_INVALID_FAILURE = "contract-invalid-failure"
    MIXED = "mixed"
    STALE = "stale"
    INCOMPLETE = "incomplete"
    VALID = "valid"


class EvidenceClassifyRequest(BaseModel):
    """Request for evidence classification."""
    evidence_id: str
    evidence_type: EvidenceType
    data: Dict[str, Any] = Field(..., description="Evidence data to classify")
    timestamp: Optional[str] = Field(default=None, description="Evidence timestamp (ISO format)")
    max_age_hours: int = Field(default=24, ge=1, le=168, description="Maximum evidence age in hours")
    
    class Config:
        json_schema_extra = {
            "example": {
                "evidence_id": "evidence_001",
                "evidence_type": "gate_check",
                "data": {
                    "dev_status": 200,
                    "crv_status": 200,
                    "product_status": 200,
                    "environment": "staging"
                },
                "timestamp": "2026-02-17T10:00:00Z",
                "max_age_hours": 24
            }
        }


class EvidenceDetails(BaseModel):
    """Detailed evidence analysis."""
    is_fresh: bool
    age_hours: Optional[float]
    completeness_score: float  # 0-100
    quality_indicators: Dict[str, bool]
    missing_fields: list[str]
    warnings: list[str]


class EvidenceClassifyResponse(BaseModel):
    """Response from evidence classification."""
    evidence_id: str
    classification: EvidenceClassification
    confidence: float  # 0-1
    details: EvidenceDetails
    summary: str
    recommendations: list[str]
    timestamp: str


class EvidenceClassificationService:
    """Service for evidence classification logic."""
    
    @staticmethod
    def classify_evidence(
        evidence_id: str,
        evidence_type: EvidenceType,
        data: Dict[str, Any],
        timestamp: Optional[str] = None,
        max_age_hours: int = 24
    ) -> EvidenceClassifyResponse:
        """
        Classify evidence based on type, freshness, and content.
        
        Classification logic:
        - Gate checks: Based on status codes (contract-valid-success, contract-valid-failure, contract-invalid-failure, mixed)
        - Backtest: Based on metric completeness and values
        - Validation: Based on completion status and results
        - Stale: If evidence exceeds max_age_hours
        - Incomplete: If required fields are missing
        """
        warnings = []
        missing_fields = []
        quality_indicators = {}
        
        # Parse timestamp and check freshness
        evidence_ts = None
        if timestamp:
            try:
                evidence_ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                if evidence_ts.tzinfo is None:
                    evidence_ts = evidence_ts.replace(tzinfo=timezone.utc)
            except Exception:
                warnings.append("Invalid timestamp format")
        
        now = datetime.now(timezone.utc)
        is_fresh = True
        age_hours = None
        
        if evidence_ts:
            age_seconds = (now - evidence_ts).total_seconds()
            age_hours = age_seconds / 3600
            is_fresh = age_hours <= max_age_hours
            if not is_fresh:
                warnings.append(f"Evidence is {age_hours:.1f} hours old (max: {max_age_hours})")
        else:
            warnings.append("No timestamp provided - cannot verify freshness")
        
        # Classify based on evidence type
        classification = None
        confidence = 1.0
        recommendations = []
        
        if evidence_type == EvidenceType.GATE_CHECK:
            classification, conf = EvidenceClassificationService._classify_gate_check(data, quality_indicators, missing_fields)
            confidence = conf
        elif evidence_type == EvidenceType.BACKTEST:
            classification, conf = EvidenceClassificationService._classify_backtest(data, quality_indicators, missing_fields)
            confidence = conf
        elif evidence_type == EvidenceType.VALIDATION:
            classification, conf = EvidenceClassificationService._classify_validation(data, quality_indicators, missing_fields)
            confidence = conf
        elif evidence_type == EvidenceType.ACCEPTANCE_TEST:
            classification, conf = EvidenceClassificationService._classify_acceptance_test(data, quality_indicators, missing_fields)
            confidence = conf
        elif evidence_type == EvidenceType.PRODUCTION_METRICS:
            classification, conf = EvidenceClassificationService._classify_production_metrics(data, quality_indicators, missing_fields)
            confidence = conf
        else:
            classification = EvidenceClassification.INCOMPLETE
            confidence = 0.5
            warnings.append(f"Unknown evidence type: {evidence_type}")
        
        # Override with stale if not fresh
        if not is_fresh and classification not in [EvidenceClassification.STALE, EvidenceClassification.INCOMPLETE]:
            recommendations.append("Regenerate evidence - current evidence is stale")
        
        # Check completeness
        if missing_fields:
            if classification != EvidenceClassification.INCOMPLETE:
                warnings.append(f"Missing {len(missing_fields)} required fields")
                confidence *= 0.8
        
        # Calculate completeness score
        total_quality = len(quality_indicators)
        passed_quality = sum(1 for v in quality_indicators.values() if v)
        completeness_score = (passed_quality / total_quality * 100) if total_quality > 0 else 0
        
        # Generate recommendations
        if classification == EvidenceClassification.CONTRACT_VALID_FAILURE:
            recommendations.append("Fix failing checks before promoting to production")
        elif classification == EvidenceClassification.CONTRACT_INVALID_FAILURE:
            recommendations.append("Critical failure - investigate contract violations")
        elif classification == EvidenceClassification.MIXED:
            recommendations.append("Resolve mixed results - ensure all checks pass")
        elif classification == EvidenceClassification.INCOMPLETE:
            recommendations.append(f"Complete missing fields: {', '.join(missing_fields)}")
        
        if not recommendations:
            recommendations.append("Evidence is valid and ready for use")
        
        # Generate summary
        summary = f"{classification.value}: {evidence_type.value} evidence "
        if is_fresh:
            summary += f"(fresh, {completeness_score:.0f}% complete)"
        else:
            summary += f"(stale, {age_hours:.1f}h old)"
        
        return EvidenceClassifyResponse(
            evidence_id=evidence_id,
            classification=classification,
            confidence=confidence,
            details=EvidenceDetails(
                is_fresh=is_fresh,
                age_hours=age_hours,
                completeness_score=completeness_score,
                quality_indicators=quality_indicators,
                missing_fields=missing_fields,
                warnings=warnings
            ),
            summary=summary,
            recommendations=recommendations,
            timestamp=datetime.utcnow().isoformat()
        )
    
    @staticmethod
    def _classify_gate_check(data: Dict[str, Any], quality_indicators: Dict[str, bool], missing_fields: list[str]) -> tuple[EvidenceClassification, float]:
        """Classify gate check evidence based on status codes."""
        dev_status = data.get("dev_status")
        crv_status = data.get("crv_status")
        product_status = data.get("product_status")
        
        quality_indicators["has_dev_status"] = dev_status is not None
        quality_indicators["has_crv_status"] = crv_status is not None
        quality_indicators["has_product_status"] = product_status is not None
        quality_indicators["has_environment"] = "environment" in data
        
        if dev_status is None:
            missing_fields.append("dev_status")
        if crv_status is None:
            missing_fields.append("crv_status")
        if product_status is None:
            missing_fields.append("product_status")
        
        if missing_fields:
            return EvidenceClassification.INCOMPLETE, 0.3
        
        # Convert to int for comparison
        dev = int(dev_status or 0)
        crv = int(crv_status or 0)
        product = int(product_status or 0)
        
        # Classification logic matching parse_acceptance_evidence_metadata
        if dev == 200 and crv == 200 and product == 200:
            return EvidenceClassification.CONTRACT_VALID_SUCCESS, 1.0
        elif dev == 200 and crv in {404, 422} and product in {404, 422}:
            return EvidenceClassification.CONTRACT_VALID_FAILURE, 0.9
        elif any(code >= 500 for code in (dev, crv, product)) or dev == 0:
            return EvidenceClassification.CONTRACT_INVALID_FAILURE, 0.7
        else:
            return EvidenceClassification.MIXED, 0.6
    
    @staticmethod
    def _classify_backtest(data: Dict[str, Any], quality_indicators: Dict[str, bool], missing_fields: list[str]) -> tuple[EvidenceClassification, float]:
        """Classify backtest evidence."""
        required_fields = ["sharpe_ratio", "max_drawdown", "total_return", "num_trades"]
        
        for field in required_fields:
            has_field = field in data and data[field] is not None
            quality_indicators[f"has_{field}"] = has_field
            if not has_field:
                missing_fields.append(field)
        
        if missing_fields:
            return EvidenceClassification.INCOMPLETE, 0.3
        
        # Check quality thresholds
        sharpe = data.get("sharpe_ratio", 0)
        drawdown = data.get("max_drawdown", 1.0)
        num_trades = data.get("num_trades", 0)
        
        quality_indicators["sharpe_positive"] = sharpe > 0
        quality_indicators["drawdown_acceptable"] = drawdown < 0.5
        quality_indicators["sufficient_trades"] = num_trades >= 10
        
        if sharpe > 0 and drawdown < 0.5 and num_trades >= 10:
            return EvidenceClassification.VALID, 1.0
        else:
            return EvidenceClassification.CONTRACT_VALID_FAILURE, 0.7
    
    @staticmethod
    def _classify_validation(data: Dict[str, Any], quality_indicators: Dict[str, bool], missing_fields: list[str]) -> tuple[EvidenceClassification, float]:
        """Classify validation evidence."""
        status = data.get("status")
        quality_indicators["has_status"] = status is not None
        
        if status is None:
            missing_fields.append("status")
            return EvidenceClassification.INCOMPLETE, 0.3
        
        quality_indicators["completed"] = status == "completed"
        quality_indicators["has_metrics"] = "metrics" in data
        
        if status == "completed":
            return EvidenceClassification.VALID, 1.0
        elif status == "failed":
            return EvidenceClassification.CONTRACT_VALID_FAILURE, 0.8
        else:
            return EvidenceClassification.INCOMPLETE, 0.5
    
    @staticmethod
    def _classify_acceptance_test(data: Dict[str, Any], quality_indicators: Dict[str, bool], missing_fields: list[str]) -> tuple[EvidenceClassification, float]:
        """Classify acceptance test evidence."""
        passed = data.get("passed")
        quality_indicators["has_result"] = passed is not None
        
        if passed is None:
            missing_fields.append("passed")
            return EvidenceClassification.INCOMPLETE, 0.3
        
        quality_indicators["all_tests_passed"] = passed is True
        
        if passed:
            return EvidenceClassification.CONTRACT_VALID_SUCCESS, 1.0
        else:
            return EvidenceClassification.CONTRACT_VALID_FAILURE, 0.9
    
    @staticmethod
    def _classify_production_metrics(data: Dict[str, Any], quality_indicators: Dict[str, bool], missing_fields: list[str]) -> tuple[EvidenceClassification, float]:
        """Classify production metrics evidence."""
        required_fields = ["uptime", "error_rate", "latency_p95"]
        
        for field in required_fields:
            has_field = field in data and data[field] is not None
            quality_indicators[f"has_{field}"] = has_field
            if not has_field:
                missing_fields.append(field)
        
        if missing_fields:
            return EvidenceClassification.INCOMPLETE, 0.3
        
        uptime = data.get("uptime", 0)
        error_rate = data.get("error_rate", 1.0)
        
        quality_indicators["high_uptime"] = uptime >= 0.99
        quality_indicators["low_error_rate"] = error_rate <= 0.01
        
        if uptime >= 0.99 and error_rate <= 0.01:
            return EvidenceClassification.VALID, 1.0
        else:
            return EvidenceClassification.CONTRACT_VALID_FAILURE, 0.7
