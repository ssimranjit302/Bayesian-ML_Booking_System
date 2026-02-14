import numpy as np

def posterior_occupancy(prior, observed=1):
    """
    Compute posterior P(X | Y=observed)
    prior: array of length N+1
    observed: 1 if slot present, 0 if missing
    """
    prior = np.array(prior)
    if observed == 1:
        # exclude X=30 for observed present
        posterior = prior[:-1]  # X=0..29
    else:
        # observed missing => X=30
        posterior = np.zeros_like(prior)
        posterior[-1] = 1.0
    posterior /= posterior.sum()
    return posterior


def estimate_X(posterior, method="mean"):
    if method == "mean":
        return np.sum(np.arange(len(posterior)) * posterior)
    elif method == "map":
        return np.argmax(posterior)
    else:
        raise ValueError("method must be 'mean' or 'map'")
