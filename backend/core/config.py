import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


def _get_db_url(async_driver: bool = True) -> str:
    # On Vercel / serverless runtimes, root is read-only; use /tmp for writable SQLite
    is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
    db_file = "/tmp/revive.db" if is_serverless else "./revive.db"
    return f"sqlite+aiosqlite:///{db_file}" if async_driver else f"sqlite:///{db_file}"


class Settings(BaseSettings):
    PROJECT_NAME: str = "REVIVE — Policy-Governed AI Revenue Recovery Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = _get_db_url(async_driver=True)
    SYNC_DATABASE_URL: str = _get_db_url(async_driver=False)
    
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
