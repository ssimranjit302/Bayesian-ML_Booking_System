import argparse
import json
import math
import pandas as pd
from math import comb, gamma

def beta_fn(a, b):
    # Beta(a,b) using gamma
    return gamma(a) * gamma(b) / gamma(a + b)

def beta_binomial_pmf(k, n, alpha, beta):
    # P(X=k) = C(n,k) * Beta(k+alpha, n-k+beta) / Beta(alpha,beta)
    num = comb(n, k) * beta_fn(k + alpha, n - k + beta)
    den = beta_fn(alpha, beta)
    return num / den

def detect_service_columns(df):
    # detect columns that start with 'service_'
    return [c for c in df.columns if c.startswith('service_')]

def build_priors(df, n_seats=30, S=20, min_samples=5, use_dayofweek=False):
    """
    Returns dict keyed by "service|hour" (string) -> dict with prior info.
    If min_samples not met, uses weak uniform prior (alpha=1,beta=1).
    """
    service_cols = detect_service_columns(df)
    if not service_cols:
        raise ValueError("No service_ columns found in dataframe. Ensure compiled CSV has service_* columns.")
    priors = {}
    hours = sorted(df['hour'].dropna().unique().astype(int).tolist())
    for svc_col in service_cols:
        svc_name = svc_col.replace('service_', '')
        for hour in hours:
            # filter rows for this service and hour
            mask = (df[svc_col] == 1) & (df['hour'] == hour)
            sub = df[mask]
            n_total = int(len(sub))
            n_full = int(sub['Booked'].sum()) if n_total > 0 else 0
            if n_total >= min_samples:
                p_hat = n_full / n_total
                # assign alpha,beta from p_hat and S (pseudo-counts)
                alpha = max(0.001, p_hat * S)
                beta = max(0.001, (1.0 - p_hat) * S)
            else:
                # insufficient data -> weak prior
                p_hat = None
                alpha, beta = 1.0, 1.0

            # compute Beta-Binomial pmf for k=0..n_seats
            prior = [beta_binomial_pmf(k, n_seats, alpha, beta) for k in range(n_seats + 1)]
            # normalize numeric noise
            s = sum(prior)
            if s <= 0:
                # fallback to uniform
                prior = [(1.0 / (n_seats + 1)) for _ in range(n_seats + 1)]
            else:
                prior = [float(p / s) for p in prior]

            key = f"{svc_name}|{hour}"
            priors[key] = {
                "service": svc_name,
                "hour": int(hour),
                "alpha": float(alpha),
                "beta": float(beta),
                "p_hat": float(p_hat) if p_hat is not None else None,
                "n_total": n_total,
                "n_full": n_full,
                "prior": prior
            }
    return priors

def save_priors(priors, out_path):
    with open(out_path, 'w') as f:
        json.dump(priors, f, indent=2)

def load_compiled_csv(path):
    df = pd.read_csv(path, parse_dates=['datetime'])
    # normalize booleans (TRUE/FALSE) and boolean types to 1/0
    for c in df.columns:
        if df[c].dtype == object:
            vals = df[c].dropna().unique()
            if set(map(str, vals)).issubset({'TRUE','FALSE','True','False'}):
                df[c] = df[c].map(lambda x: 1 if str(x).upper()=='TRUE' else 0)
    # ensure one-hot service columns are integers
    service_cols = detect_service_columns(df)
    for c in service_cols:
        if df[c].dtype == bool:
            df[c] = df[c].astype(int)
    # ensure essential columns exist
    for req in ['hour','Booked']:
        if req not in df.columns:
            raise ValueError(f"Required column '{req}' not found in compiled CSV.")
    df['hour'] = pd.to_numeric(df['hour'], errors='coerce').fillna(0).astype(int)
    df['Booked'] = pd.to_numeric(df['Booked'], errors='coerce').fillna(0).astype(int)
    return df

def main():
    parser = argparse.ArgumentParser(description="Build Beta-Binomial priors per (service, hour).")
    parser.add_argument("--input", type=str, default="compiled.csv", help="Path to compiled CSV")
    parser.add_argument("--out", type=str, default="priors.json", help="Output JSON file for priors")
    parser.add_argument("--S", type=float, default=20.0, help="Pseudo-count (alpha+beta) when constructing Beta prior")
    parser.add_argument("--min-samples", type=int, default=5, help="Minimum samples to trust p_hat; otherwise use weak prior")
    parser.add_argument("--n-seats", type=int, default=30, help="Number of seats in a slot")
    args = parser.parse_args()

    df = load_compiled_csv(args.input)
    priors = build_priors(df, n_seats=args.n_seats, S=args.S, min_samples=args.min_samples)
    save_priors(priors, args.out)
    print(f"Saved priors for {len(priors)} (service,hour) pairs to {args.out}")

if __name__ == "__main__":
    main()
