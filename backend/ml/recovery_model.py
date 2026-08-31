"""
Logistic Regression recovery model training, persistence, and inference engine.
Prioritizes regulatory interpretability and direct coefficient extraction.
"""
import os
import joblib
import numpy as np
from typing import Dict, Any, Tuple, List
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, brier_score_loss, classification_report
from backend.core.config import settings
from backend.ml.dataset_generator import generate_synthetic_data
from backend.ml.feature_pipeline import (
    FEATURE_NAMES,
    FEATURE_LABELS,
    extract_features,
    generate_feature_explanations,
)


class RecoveryModel:
    def __init__(self, model_path: str = settings.MODEL_PATH):
        self.model_path = model_path
        self.model: LogisticRegression = None
        self.feature_names = FEATURE_NAMES
        self.metrics: Dict[str, Any] = {}
        
        # Load or train
        if os.path.exists(self.model_path):
            self.load()
        else:
            self.train_and_save()

    def train_and_save(self, num_records: int = 6000, seed: int = 42) -> Dict[str, Any]:
        """
        Trains Logistic Regression model with L2 regularization on synthetic dataset.
        """
        customers, transactions = generate_synthetic_data(num_records=num_records, seed=seed)
        cust_map = {c["customer_id"]: c for c in customers}

        X = []
        y = []
        for tx in transactions:
            c = cust_map.get(tx["customer_id"])
            feat = extract_features(tx, c)
            X.append(feat)
            y.append(tx["actual_recovered"])

        X = np.array(X)
        y = np.array(y)

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.20, random_state=seed, stratify=y
        )

        clf = LogisticRegression(
            C=1.0,
            penalty="l2",
            solver="lbfgs",
            max_iter=1000,
            random_state=seed
        )
        clf.fit(X_train, y_train)

        # Evaluate
        y_pred_proba = clf.predict_proba(X_test)[:, 1]
        y_pred = clf.predict(X_test)
        auc = float(roc_auc_score(y_test, y_pred_proba))
        brier = float(brier_score_loss(y_test, y_pred_proba))

        self.model = clf
        self.metrics = {
            "roc_auc": round(auc, 4),
            "brier_score": round(brier, 4),
            "total_samples": len(X),
            "train_samples": len(X_train),
            "test_samples": len(X_test),
            "positive_recovery_rate": round(float(np.mean(y)), 4),
        }

        # Ensure directory exists and persist
        os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
        joblib.dump({"model": self.model, "metrics": self.metrics}, self.model_path)
        print(f"[ML Engine] Trained and saved Logistic Regression Model (ROC-AUC: {auc:.4f})")
        return self.metrics

    def load(self):
        """Loads saved joblib artifact."""
        try:
            artifact = joblib.load(self.model_path)
            self.model = artifact["model"]
            self.metrics = artifact.get("metrics", {})
        except Exception as e:
            print(f"[ML Engine] Failed to load model from {self.model_path}: {e}. Retraining...")
            self.train_and_save()

    def predict_probability(self, tx_data: Dict[str, Any], customer_data: Dict[str, Any] = None) -> Tuple[float, List[Dict[str, Any]]]:
        """
        Predicts recovery probability and generates the waterfall explanation breakdown.
        """
        if self.model is None:
            self.load()

        feat = extract_features(tx_data, customer_data)
        feat_2d = feat.reshape(1, -1)
        prob = float(self.model.predict_proba(feat_2d)[0, 1])

        coeffs = self.model.coef_[0]
        intercept = float(self.model.intercept_[0])
        breakdown = generate_feature_explanations(feat, coeffs, intercept)

        return round(prob, 4), breakdown

    def get_global_weights(self) -> List[Dict[str, Any]]:
        """
        Returns global model weights and odds ratios for UI inspection.
        """
        if self.model is None:
            self.load()

        coeffs = self.model.coef_[0]
        weights = []
        for i, name in enumerate(self.feature_names):
            c = float(coeffs[i])
            odds_ratio = float(np.exp(c))
            weights.append({
                "feature": name,
                "label": FEATURE_LABELS.get(name, name),
                "coefficient": round(c, 4),
                "odds_ratio": round(odds_ratio, 4),
                "impact_direction": "POSITIVE" if c > 0 else "NEGATIVE",
            })
        weights.sort(key=lambda x: abs(x["coefficient"]), reverse=True)
        return weights


# Global Singleton Model instance
ml_model = RecoveryModel()
