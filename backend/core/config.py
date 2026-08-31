from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str = "REVIVE — Autonomous AI Revenue Recovery Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./revive.db"
    SYNC_DATABASE_URL: str = "sqlite:///./revive.db"
    
    # Machine Learning
    MODEL_PATH: str = "./backend/ml/recovery_model.joblib"
    SYNTHETIC_DATASET_SIZE: int = 6000
    RANDOM_SEED: int = 42
    
    # LLM Settings (Optional - fallback engine used when not configured)
    OPENAI_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    LLM_MODEL: str = "gemini-1.5-flash"
    
    # Deterministic Policy Thresholds (Locked Fintech Guardrails)
    MAX_RETRY_COUNT: int = 3
    HIGH_VALUE_THRESHOLD: float = 10000.0  # INR > 10,000 requires human approval
    LOW_RECOVERY_PROB_THRESHOLD: float = 0.15  # < 15% halts recovery to save fees
    HIGH_CHURN_RISK_THRESHOLD: float = 0.65
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
