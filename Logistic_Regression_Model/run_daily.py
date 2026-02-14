from bayesian_model import BayesianSlotModel
from decision import detect_full_slot
from occupancy_estimator import posterior_occupancy, estimate_X

model = BayesianSlotModel("priors.json")

service = "Cryotherapy"
hour = 15

p_full = model.predict_prob(service, hour)
decision = detect_full_slot(p_full)

slot = model.model[f"{service}|{hour}"]

if decision == 0:
    posterior = posterior_occupancy(slot["prior"], p_full)
    x_hat = estimate_X(posterior, method="mean")
    print(f"Estimated bookings: {x_hat:.1f}/30")
else:
    print("Slot predicted FULL → X = 30")
