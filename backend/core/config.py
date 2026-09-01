import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


import shutil

def _ensure_db_initialized() -> str:
    is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
    if not is_serverless:
        return "./revive.db"
    
    tmp_db = "/tmp/revive.db"
    if not os.path.exists(tmp_db):
        root_db = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "revive.db")
        if os.path.exists(root_db):
            try:
                shutil.copyfile(root_db, tmp_db)
            except Exception as e:
                print(f"[Config Warning] Failed to copy pre-seeded DB: {e}")
    return tmp_db


def _get_db_url(async_driver: bool = True) -> str:
    db_file = _ensure_db_initialized()
    return f"sqlite+aiosqlite:///{db_file}" if async_driver else f"sqlite:///{db_file}"


def _get_model_path() -> str:
    is_serverless = bool(os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
    packaged_model = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml", "recovery_model.joblib")
    if os.path.exists(packaged_model):
        return packaged_model
    return "/tmp/recovery_model.joblib" if is_serverless else "./backend/ml/recovery_model.joblib"


class Settings(BaseSettings):
    PROJECT_NAME: str = "REVIVE — Policy-Governed AI Revenue Recovery Agent"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = _get_db_url(async_driver=True)
    SYNC_DATABASE_URL: str = _get_db_url(async_driver=False)
    
    # Machine Learning
    MODEL_PATH: str = _get_model_path()
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
