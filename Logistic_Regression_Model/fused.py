import json
import joblib
import numpy as np
from bayesian_model import BayesianSlotModel
from occupancy_estimator import posterior_occupancy, estimate_X

# ---------------------------
# Load Bayesian model (historical priors or previous posteriors)
# ---------------------------
# If posteriors.json exists, use it; otherwise, fall back to priors.json
import pathlib
if pathlib.Path("posteriors.json").exists():
    bayes_path = "posteriors.json"
else:
    bayes_path = "priors.json"

model = BayesianSlotModel(bayes_path)

# ---------------------------
# Load ML model
# ---------------------------
ml_data = joblib.load("improved_logistic_pipeline.joblib")
ml_model = ml_data["model"]
threshold = ml_data["threshold"]
features = ml_data["features"]

# ---------------------------
# Define slots to check (example)
# ---------------------------
# In practice, fetch this dynamically from Playwright
slots = [
    {"service": "Cryotherapy", "hour": 9},
    {"service": "Cryotherapy", "hour": 15}
]

# ---------------------------
# Iterate over slots
# ---------------------------
for slot_info in slots:
    service = slot_info["service"]
    hour = slot_info["hour"]

    key = f"{service}|{hour}"
    bayes_slot = model.model[key]

    # ---------------------------
    # ML Prediction
    # ---------------------------
    # Construct feature vector for this slot
    # Here, we just use a dummy DataFrame with one row; in practice use actual features
    import pandas as pd
    X_slot = pd.DataFrame([{f: 0 for f in features}])
    if f"service_{service}" in features:
        X_slot[f"service_{service}"] = 1
    X_slot["hour"] = hour

    p_ml = ml_model.predict_proba(X_slot)[0, 1]  # P(full | features)
    decision_ml = int(p_ml >= threshold)

    # ---------------------------
    # Fuse ML probability with Bayesian prior
    # ---------------------------
    # Augment the Beta-Binomial prior with ML pseudo-count for fully booked slot
    # Treat ML prediction as pseudo-observation for X=30
    prior_probs = bayes_slot["prior"].copy()
    n_seats = len(prior_probs) - 1

    # P(X=30) = p_ml, scale remaining probabilities to sum to (1 - p_ml)
    augmented_prior = prior_probs.copy()
    augmented_prior[-1] = p_ml
    remaining_sum = 1 - p_ml
    for i in range(n_seats):
        augmented_prior[i] = augmented_prior[i] * remaining_sum / sum(prior_probs[:-1])

    # ---------------------------
    # Posterior estimation
    # ---------------------------
    if decision_ml == 0:
        posterior = posterior_occupancy(augmented_prior)
        x_hat = estimate_X(posterior, method="mean")
        print(f"{service} @ {hour}:00 → Estimated bookings: {x_hat:.1f}/{n_seats}")
        observed_full = 0
    else:
        print(f"{service} @ {hour}:00 → Predicted FULL → X = {n_seats}")
        observed_full = 1

    # ---------------------------
    # Update Bayesian counts
    # ---------------------------
    model.update(service, hour, observed_full)

# ---------------------------
# Save updated posteriors
# ---------------------------
model.save("posteriors.json")
print("Updated posteriors saved to posteriors.json")
