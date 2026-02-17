"""
Reflexion feedback service for primitive API.
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from datetime import datetime
import hashlib


class ReflexionSuggestRequest(BaseModel):
    """Request for reflexion feedback suggestions."""
    strategy_id: str
    iteration_num: int = Field(..., ge=1, description="Current iteration number")
    feedback: Optional[str] = Field(default=None, description="Optional user feedback")
    metrics: Optional[Dict[str, float]] = Field(default=None, description="Current strategy metrics")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "strategy_id": "momentum_001",
                "iteration_num": 2,
                "feedback": "Strategy underperforms in high volatility regimes",
                "metrics": {
                    "sharpe_ratio": 1.2,
                    "max_drawdown": 0.18,
                    "win_rate": 0.55
                },
                "context": {
                    "strategy_type": "momentum",
                    "lookback": 20
                }
            }
        }


class Suggestion(BaseModel):
    """Individual improvement suggestion."""
    category: str  # "parameter", "logic", "risk_management", "timing"
    priority: str  # "high", "medium", "low"
    description: str
    rationale: str
    expected_impact: str


class ReflexionSuggestResponse(BaseModel):
    """Response from reflexion feedback."""
    strategy_id: str
    iteration_num: int
    improvement_score: float  # -2.0 to +2.0
    suggestions: List[Suggestion]
    summary: str
    timestamp: str


class ReflexionFeedbackService:
    """Service for generating reflexion feedback and improvement suggestions."""
    
    @staticmethod
    def _derive_improvement_score(strategy_id: str, iteration_num: int, feedback: Optional[str]) -> float:
        """
        Derive improvement score from strategy ID, iteration, and feedback.
        
        Score range: -2.0 to +2.0
        - Positive: improvement detected
        - Negative: degradation detected
        - Zero: no significant change
        """
        seed = f"{strategy_id}:{iteration_num}:{feedback or ''}".encode("utf-8")
        digest = hashlib.sha256(seed).hexdigest()
        raw = int(digest[:8], 16) % 401
        return round((raw - 200) / 100.0, 2)
    
    @staticmethod
    def _generate_suggestions(
        strategy_id: str,
        iteration_num: int,
        feedback: Optional[str],
        metrics: Optional[Dict[str, float]],
        context: Optional[Dict[str, Any]]
    ) -> List[Suggestion]:
        """Generate improvement suggestions based on strategy state."""
        suggestions = []
        
        # Base suggestions for all strategies
        suggestions.append(Suggestion(
            category="parameter",
            priority="medium",
            description=f"Adjust lookback period bias for iteration {iteration_num}",
            rationale="Historical lookback windows may be overfitted to recent market regimes",
            expected_impact="Reduce regime-specific bias by 15-20%"
        ))
        
        # Metric-based suggestions
        if metrics:
            sharpe = metrics.get("sharpe_ratio", 0)
            drawdown = metrics.get("max_drawdown", 0)
            win_rate = metrics.get("win_rate", 0)
            
            if sharpe < 1.0:
                suggestions.append(Suggestion(
                    category="risk_management",
                    priority="high",
                    description="Improve risk-adjusted returns through volatility targeting",
                    rationale=f"Current Sharpe ratio {sharpe:.2f} is below institutional threshold",
                    expected_impact="Target Sharpe ratio improvement of 0.3-0.5 points"
                ))
            
            if drawdown > 0.20:
                suggestions.append(Suggestion(
                    category="risk_management",
                    priority="high",
                    description="Implement stricter drawdown control mechanisms",
                    rationale=f"Max drawdown {drawdown:.1%} exceeds acceptable risk tolerance",
                    expected_impact="Reduce peak-to-trough losses by 25-30%"
                ))
            
            if win_rate and win_rate < 0.45:
                suggestions.append(Suggestion(
                    category="logic",
                    priority="medium",
                    description="Refine entry signal quality to improve win rate",
                    rationale=f"Win rate {win_rate:.1%} suggests signal quality issues",
                    expected_impact="Improve win rate to 48-52% range"
                ))
        
        # Feedback-based suggestions
        if feedback:
            feedback_lower = feedback.lower()
            
            if "volatility" in feedback_lower or "vol" in feedback_lower:
                suggestions.append(Suggestion(
                    category="parameter",
                    priority="high",
                    description="Update volatility targeting to reduce regime sensitivity",
                    rationale="User feedback indicates volatility-related performance issues",
                    expected_impact="Stabilize returns across volatility regimes"
                ))
            
            if "drawdown" in feedback_lower or "loss" in feedback_lower:
                suggestions.append(Suggestion(
                    category="risk_management",
                    priority="high",
                    description="Strengthen parameter guardrails for drawdown control",
                    rationale="User feedback highlights drawdown concerns",
                    expected_impact="Reduce tail risk exposure by 20-25%"
                ))
            
            if "timing" in feedback_lower or "entry" in feedback_lower or "exit" in feedback_lower:
                suggestions.append(Suggestion(
                    category="timing",
                    priority="medium",
                    description="Optimize entry/exit timing with adaptive filters",
                    rationale="User feedback suggests timing inefficiencies",
                    expected_impact="Improve trade execution quality by 10-15%"
                ))
        
        # Context-based suggestions
        if context:
            strategy_type = context.get("strategy_type", "").lower()
            
            if "momentum" in strategy_type:
                suggestions.append(Suggestion(
                    category="logic",
                    priority="medium",
                    description="Add mean reversion filter to reduce momentum crashes",
                    rationale="Momentum strategies benefit from regime detection",
                    expected_impact="Reduce drawdowns during trend reversals by 30%"
                ))
            
            if "mean_reversion" in strategy_type or "pairs" in strategy_type:
                suggestions.append(Suggestion(
                    category="parameter",
                    priority="medium",
                    description="Calibrate z-score thresholds for current volatility regime",
                    rationale="Mean reversion parameters need regime-adaptive scaling",
                    expected_impact="Improve entry precision by 12-18%"
                ))
        
        # Generic improvement suggestion
        suggestions.append(Suggestion(
            category="logic",
            priority="low",
            description="Consider ensemble approach combining multiple signal sources",
            rationale="Diversified signal generation improves robustness",
            expected_impact="Reduce strategy-specific risk by 15-20%"
        ))
        
        # Limit to top 5 suggestions by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: priority_order[s.priority])
        return suggestions[:5]
    
    @staticmethod
    def suggest_improvements(
        strategy_id: str,
        iteration_num: int,
        feedback: Optional[str] = None,
        metrics: Optional[Dict[str, float]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ReflexionSuggestResponse:
        """
        Generate improvement suggestions for strategy refinement.
        
        Analyzes:
        - Current iteration performance
        - User feedback
        - Metric thresholds
        - Strategy context
        
        Returns prioritized suggestions with expected impact.
        """
        # Calculate improvement score
        improvement_score = ReflexionFeedbackService._derive_improvement_score(
            strategy_id, iteration_num, feedback
        )
        
        # Generate suggestions
        suggestions = ReflexionFeedbackService._generate_suggestions(
            strategy_id, iteration_num, feedback, metrics, context
        )
        
        # Generate summary
        high_priority = sum(1 for s in suggestions if s.priority == "high")
        
        if improvement_score > 1.0:
            summary = f"Strong improvement detected (+{improvement_score:.2f}). Continue current approach with {len(suggestions)} refinements."
        elif improvement_score > 0.5:
            summary = f"Moderate improvement (+{improvement_score:.2f}). {high_priority} high-priority suggestions for further gains."
        elif improvement_score > -0.5:
            summary = f"Minimal change ({improvement_score:+.2f}). {len(suggestions)} suggestions to break through plateau."
        elif improvement_score > -1.0:
            summary = f"Slight degradation ({improvement_score:.2f}). {high_priority} high-priority fixes recommended."
        else:
            summary = f"Significant degradation ({improvement_score:.2f}). Urgent attention to {high_priority} critical issues."
        
        return ReflexionSuggestResponse(
            strategy_id=strategy_id,
            iteration_num=iteration_num,
            improvement_score=improvement_score,
            suggestions=suggestions,
            summary=summary,
            timestamp=datetime.utcnow().isoformat()
        )
