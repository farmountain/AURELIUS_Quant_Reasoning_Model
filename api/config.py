"""API configuration."""
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """API configuration settings."""

    # Server
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))
    api_reload: bool = os.getenv("API_RELOAD", "True").lower() == "true"

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "info")

    # Database
    db_host: str = os.getenv("DB_HOST", "localhost")
    db_port: int = int(os.getenv("DB_PORT", "5432"))
    db_name: str = os.getenv("DB_NAME", "aurelius")
    db_user: str = os.getenv("DB_USER", "aurelius")
    db_password: str = os.getenv("DB_PASSWORD", "aurelius_dev")
    db_echo: bool = os.getenv("DB_ECHO", "False").lower() == "true"

    # Feature flags
    enable_background_tasks: bool = True
    enable_mock_data: bool = True
    enable_truth_backtests: bool = os.getenv("ENABLE_TRUTH_BACKTESTS", "true").lower() == "true"
    enable_truth_validation: bool = os.getenv("ENABLE_TRUTH_VALIDATION", "true").lower() == "true"
    enable_truth_gates: bool = os.getenv("ENABLE_TRUTH_GATES", "true").lower() == "true"
    
    # Primitive API feature flags (for gradual rollout)
    enable_primitive_determinism: bool = os.getenv("ENABLE_PRIMITIVE_DETERMINISM", "false").lower() == "true"
    enable_primitive_risk: bool = os.getenv("ENABLE_PRIMITIVE_RISK", "false").lower() == "true"
    enable_primitive_policy: bool = os.getenv("ENABLE_PRIMITIVE_POLICY", "false").lower() == "true"
    enable_primitive_strategy: bool = os.getenv("ENABLE_PRIMITIVE_STRATEGY", "false").lower() == "true"
    enable_primitive_evidence: bool = os.getenv("ENABLE_PRIMITIVE_EVIDENCE", "false").lower() == "true"
    enable_primitive_gates: bool = os.getenv("ENABLE_PRIMITIVE_GATES", "false").lower() == "true"
    enable_primitive_reflexion: bool = os.getenv("ENABLE_PRIMITIVE_REFLEXION", "false").lower() == "true"
    enable_primitive_orchestrator: bool = os.getenv("ENABLE_PRIMITIVE_ORCHESTRATOR", "false").lower() == "true"
    enable_primitive_readiness: bool = os.getenv("ENABLE_PRIMITIVE_READINESS", "false").lower() == "true"
    
    # Dashboard migration flags (traffic percentage to primitive APIs)
    dashboard_primitives_traffic_pct: int = int(os.getenv("DASHBOARD_PRIMITIVES_TRAFFIC_PCT", "0"))

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "allow"  # Allow extra fields from .env


settings = Settings()
