import json
from pathlib import Path

class BayesianSlotModel:
    def __init__(self, priors_path="priors.json"):
        self.priors_path = Path(priors_path)
        with open(self.priors_path, "r") as f:
            self.model = json.load(f)

    def predict_prob(self, service, hour):
        key = f"{service}|{hour}"
        p = self.model[key]
        return p["alpha"] / (p["alpha"] + p["beta"])

    def update(self, service, hour, is_full):
        key = f"{service}|{hour}"
        p = self.model[key]

        if is_full:
            p["alpha"] += 1
            p["n_full"] += 1
        else:
            p["beta"] += 1

        p["n_total"] += 1
        p["p_hat"] = p["alpha"] / (p["alpha"] + p["beta"])

        return p["p_hat"]

    def save(self, out_path="posteriors.json"):
        with open(out_path, "w") as f:
            json.dump(self.model, f, indent=2)
