"""
ML Model Explainability and Inspection API router.
"""
from fastapi import APIRouter
from backend.ml.recovery_model import ml_model

router = APIRouter(prefix="/ml", tags=["Machine Learning"])


@router.get("/weights")
async def get_model_weights():
    """Returns global logistic regression coefficients and odds ratios for interpretability."""
    return {
        "metrics": ml_model.metrics,
        "weights": ml_model.get_global_weights()
    }


@router.get("/metrics")
async def get_model_metrics():
    """Returns training metrics (ROC-AUC, Brier score, sample sizes)."""
    return ml_model.metrics


@router.post("/retrain")
async def retrain_model():
    """Retrains the model on the 6,000 synthetic dataset records."""
    metrics = ml_model.train_and_save()
    return {
        "status": "SUCCESS",
        "message": "Logistic Regression model successfully retrained",
        "metrics": metrics,
    }
