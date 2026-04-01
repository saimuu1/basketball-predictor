"""
train_model.py
Trains an sklearn model on the prepared dataset and saves model.pkl.

Usage (from backend/ directory):
    python -m app.scripts.train_model
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config import MODEL_DIR, MODEL_PATH, MODEL_DATASET_PATH
from app.services.predictor import FEATURE_COLUMNS

RANDOM_STATE = 42
TEST_SIZE = 0.2


def main() -> None:
    print(f"Loading dataset from: {MODEL_DATASET_PATH}")
    if not MODEL_DATASET_PATH.exists():
        print("ERROR: Dataset not found. Run `python -m scripts.build_dataset` first.")
        sys.exit(1)

    df = pd.read_csv(MODEL_DATASET_PATH)
    print(f"  {len(df)} rows, {len(df.columns)} columns.")

    # Validate columns
    missing = [c for c in FEATURE_COLUMNS if c not in df.columns]
    if missing:
        print(f"ERROR: Missing feature columns: {missing}")
        sys.exit(1)
    if "team_a_win" not in df.columns:
        print("ERROR: Missing target column 'team_a_win'.")
        sys.exit(1)

    X = df[FEATURE_COLUMNS].fillna(0.0).values
    y = df["team_a_win"].values.astype(int)

    print(f"  Features shape: {X.shape}")
    print(f"  Target distribution: {np.mean(y):.3f} win rate")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=TEST_SIZE, random_state=RANDOM_STATE, stratify=y,
    )
    print(f"  Train: {len(X_train)}, Test: {len(X_test)}")

    # --- Train candidates ---
    candidates: dict[str, object] = {
        "LogisticRegression": LogisticRegression(max_iter=1000, random_state=RANDOM_STATE),
        "RandomForest": RandomForestClassifier(
            n_estimators=200, max_depth=8, random_state=RANDOM_STATE,
        ),
    }

    best_name = ""
    best_auc = -1.0
    best_model = None

    for name, model in candidates.items():
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        try:
            auc = roc_auc_score(y_test, y_proba)
        except ValueError:
            auc = 0.0

        print(f"\n  {name}:")
        print(f"    Accuracy : {acc:.4f}")
        print(f"    ROC-AUC  : {auc:.4f}")

        if auc > best_auc:
            best_auc = auc
            best_name = name
            best_model = model

    print(f"\nBest model: {best_name} (AUC={best_auc:.4f})")

    # --- Save ---
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    import joblib
    joblib.dump(best_model, MODEL_PATH)
    print(f"Model saved to: {MODEL_PATH}")

    # --- Feature importance (if available) ---
    if hasattr(best_model, "feature_importances_"):
        importances = best_model.feature_importances_
        print("\nFeature importances:")
        for col, imp in sorted(zip(FEATURE_COLUMNS, importances), key=lambda x: -x[1]):
            print(f"  {col:30s} {imp:.4f}")
    elif hasattr(best_model, "coef_"):
        coefs = best_model.coef_[0]
        print("\nLogistic Regression coefficients:")
        for col, c in sorted(zip(FEATURE_COLUMNS, coefs), key=lambda x: -abs(x[1])):
            print(f"  {col:30s} {c:+.4f}")

    print("\nDone.")


if __name__ == "__main__":
    main()
