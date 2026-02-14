# train_logistic.py
import argparse
import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import classification_report, confusion_matrix, roc_auc_score, precision_recall_curve, auc

def load_and_prepare(path):
    df = pd.read_csv(path, parse_dates=['datetime'])
    # Convert TRUE/FALSE strings to 1/0 if present
    for col in df.columns:
        if df[col].dtype == object:
            # catch 'TRUE'/'FALSE' or 'True'/'False'
            if df[col].dropna().isin(['TRUE','FALSE','True','False']).all():
                df[col] = df[col].map(lambda x: 1 if str(x).upper() == 'TRUE' else 0)
    # Ensure numeric types
    df['hour'] = pd.to_numeric(df['hour'], errors='coerce').fillna(0).astype(int)
    df['day_of_week'] = pd.to_numeric(df['day_of_week'], errors='coerce').fillna(0).astype(int)
    df['is_weekend'] = pd.to_numeric(df['is_weekend'], errors='coerce').fillna(0).astype(int)
    # If any one-hot columns are bool, convert to int
    one_hot_cols = [c for c in df.columns if c.startswith('service_') or c.startswith('room_')]
    for c in one_hot_cols:
        if df[c].dtype == bool:
            df[c] = df[c].astype(int)
    # Target
    df['Booked'] = pd.to_numeric(df['Booked'], errors='coerce').fillna(0).astype(int)
    return df

def build_pipeline(numeric_features, passthrough_features, C=1.0):
    # Scale numeric features; passthrough binary one-hot features
    preproc = ColumnTransformer([
        ('num', StandardScaler(), numeric_features),
        ('pass', 'passthrough', passthrough_features)
    ])
    # Base logistic reg with class balancing
    logreg = LogisticRegression(solver='lbfgs', max_iter=2000, class_weight='balanced', C=C, random_state=42)
    # Calibrate probabilities (improves probability estimates)
    calibrated = CalibratedClassifierCV(estimator=logreg, cv=5, method='sigmoid')
    pipeline = Pipeline([
        ('preproc', preproc),
        ('clf', calibrated)
    ])
    return pipeline

def evaluate(model, X_test, y_test):
    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)[:,1]
    print("Classification report:")
    print(classification_report(y_test, y_pred, digits=4))
    print("Confusion matrix:")
    print(confusion_matrix(y_test, y_pred))
    try:
        roc = roc_auc_score(y_test, y_proba)
        print(f"ROC AUC: {roc:.4f}")
    except Exception:
        pass
    # Precision-recall AUC
    precision, recall, _ = precision_recall_curve(y_test, y_proba)
    pr_auc = auc(recall, precision)
    print(f"PR AUC: {pr_auc:.4f}")

def main(args):
    df = load_and_prepare(args.input)
    print("Loaded rows:", len(df))
    # Drop rows with NaNs in critical cols (shouldn't be many)
    df = df.dropna(subset=['hour','day_of_week','Booked'])
    X = df.drop(columns=['datetime','Booked'])
    y = df['Booked']

    print("Class distribution (Booked=1 counts):")
    print(y.value_counts(normalize=False).to_dict())

    # Define feature groups
    numeric_features = ['hour','day_of_week','is_weekend']
    passthrough_features = [c for c in X.columns if c not in numeric_features]

    # Train/test split (stratify to preserve imbalance)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y, random_state=42)

    pipeline = build_pipeline(numeric_features, passthrough_features, C=args.C)

    print("Training model...")
    pipeline.fit(X_train, y_train)

    print("Evaluating on test set...")
    evaluate(pipeline, X_test, y_test)

    # Cross-validation (ROC AUC using pipeline's predict_proba via cross_val_score wrapper)
    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    try:
        cv_scores = cross_val_score(pipeline, X, y, cv=cv, scoring='roc_auc', n_jobs=1)
        print("Cross-val ROC AUC scores:", np.round(cv_scores,4))
        print("Mean ROC AUC:", np.round(cv_scores.mean(),4))
    except Exception as e:
        print("CV scoring failed:", e)

    # Save pipeline
    joblib.dump(pipeline, args.model_out)
    print("Saved pipeline to:", args.model_out)

    # Example: show predicted probability for last 5 rows
    example_proba = pipeline.predict_proba(X.tail(5))[:,1]
    print("Example predicted prob (last 5 rows):", np.round(example_proba, 4))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train calibrated logistic regression on booking data.")
    parser.add_argument("--input", type=str, default="compiled.csv", help="Path to compiled CSV")
    parser.add_argument("--model-out", type=str, default="logistic_pipeline.joblib", help="Path to save pipeline")
    parser.add_argument("--C", type=float, default=1.0, help="Inverse regularization strength for LogisticRegression")
    args = parser.parse_args()
    main(args)
