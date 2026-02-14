import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, StratifiedKFold, GridSearchCV
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score,
    precision_recall_curve
)
import joblib

# ---------------------------
# Load data
# ---------------------------
DATA_PATH = "compiled.csv"

df = pd.read_csv(DATA_PATH, parse_dates=["datetime"])
print("Loaded rows:", len(df))
print("Class distribution:", df["Booked"].value_counts().to_dict())

X = df.drop(columns=["Booked", "datetime"])
y = df["Booked"]

# ---------------------------
# Train / test split
# ---------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    stratify=y,
    random_state=42
)

# ---------------------------
# Base logistic model
# ---------------------------
logreg = LogisticRegression(
    solver="liblinear",
    class_weight="balanced",   # penalize false negatives more , don't miss full slots
    max_iter=1000
)

pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("clf", logreg)
])

# ---------------------------
# Hyperparameter tuning
# ---------------------------
param_grid = {
    "clf__C": [0.01, 0.05, 0.1, 0.5, 1, 5, 10]
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)

grid = GridSearchCV(
    pipeline,
    param_grid,
    scoring="roc_auc",
    cv=cv,
    n_jobs=-1
)

print("Training model with CV...")
grid.fit(X_train, y_train)

best_pipeline = grid.best_estimator_
print("Best C:", grid.best_params_)

# ---------------------------
# Probability calibration
# ---------------------------
calibrated_model = CalibratedClassifierCV(
    estimator=best_pipeline,
    method="sigmoid",
    cv=5
)

calibrated_model.fit(X_train, y_train)

# ---------------------------
# Threshold optimization
# ---------------------------
y_probs = calibrated_model.predict_proba(X_test)[:, 1]

prec, rec, thresholds = precision_recall_curve(y_test, y_probs)

# maximize F1
f1_scores = 2 * (prec * rec) / (prec + rec + 1e-9)
best_idx = np.argmax(f1_scores)
best_threshold = thresholds[best_idx]

print(f"Optimal threshold (F1-max): {best_threshold:.3f}")

# ---------------------------
# Final predictions
# ---------------------------
y_pred = (y_probs >= best_threshold).astype(int)

# ---------------------------
# Evaluation
# ---------------------------
print("\nClassification report:")
print(classification_report(y_test, y_pred))

print("Confusion matrix:")
print(confusion_matrix(y_test, y_pred))

print("ROC AUC:", roc_auc_score(y_test, y_probs))

# ---------------------------
# Save model
# ---------------------------
joblib.dump(
    {
        "model": calibrated_model,
        "threshold": best_threshold,
        "features": X.columns.tolist()
    },
    "improved_logistic_pipeline.joblib"
)

print("Saved improved model to improved_logistic_pipeline.joblib")
