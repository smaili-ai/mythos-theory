#!/usr/bin/env python3
"""
fit_scaling_laws.py — Chinchilla Scaling Law Fit for Mythos Parameter Budget

Fits the Chinchilla (Hoffmann et al., 2022) optimal scaling law against
public Mythos benchmark data to derive principled estimates for:
  - Total parameter count
  - Training token count
  - Compute budget (FLOPs)

These estimates anchor the architectural hypothesis space in docs/02.

Usage:
    python scripts/analysis/fit_scaling_laws.py
    python scripts/analysis/fit_scaling_laws.py --plot
"""

import argparse
import json
import math

try:
    import numpy as np
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

# ── Chinchilla Coefficients (Hoffmann et al., 2022) ─────────────────────────
# L(N, D) = E + A/N^alpha + B/D^beta
CHINCHILLA_E = 1.69      # Irreducible loss
CHINCHILLA_A = 406.4
CHINCHILLA_B = 410.7
CHINCHILLA_ALPHA = 0.34
CHINCHILLA_BETA = 0.28

# ── Public Benchmark Proxies for Mythos Compute ───────────────────────────────
# We estimate Mythos's compute budget by fitting against:
#  1. Prior model compute estimates (GPT-4, Claude 3 Opus).
#  2. The benchmark gap between Mythos and prior models.

# Known/estimated compute for reference models (FLOPs):
REFERENCE_MODELS = {
    "GPT-3 (175B)": {
        "flops": 3.14e23,
        "params": 175e9,
        "tokens": 300e9,
        "swe_bench_verified": 0.01,  # Not reported; effectively zero
    },
    "GPT-4 (estimate)": {
        "flops": 2.15e25,
        "params": 1.8e12,  # ~1.8T estimate (speculative)
        "tokens": 13e12,
        "swe_bench_verified": 0.49,  # Reported
    },
    "Claude 3 Opus (estimate)": {
        "flops": 5.0e24,
        "params": 2e12,
        "tokens": 5e12,
        "swe_bench_verified": 0.285,  # Reported ~28.5%
    },
    "Claude 3.5 Opus (estimate)": {
        "flops": 1.5e25,
        "params": 3e12,
        "tokens": 8e12,
        "swe_bench_verified": 0.60,  # Estimated
    },
    "Claude Mythos (target)": {
        "flops": None,  # To be derived
        "params": None,
        "tokens": None,
        "swe_bench_verified": 0.939,  # Confirmed P1
    },
}


def chinchilla_loss(n_params: float, n_tokens: float) -> float:
    """Compute predicted loss from Chinchilla scaling law."""
    return (CHINCHILLA_E
            + CHINCHILLA_A / (n_params ** CHINCHILLA_ALPHA)
            + CHINCHILLA_B / (n_tokens ** CHINCHILLA_BETA))


def optimal_params_for_compute(compute_flops: float) -> float:
    """Chinchilla-optimal model size given a compute budget (FLOPs)."""
    # N_opt ≈ (C / (6 * 20))^0.5 from the simplified Chinchilla formula
    # where C = 6 * N * D and D_opt = 20 * N
    return (compute_flops / 120.0) ** 0.5


def optimal_tokens_for_compute(compute_flops: float) -> float:
    """Chinchilla-optimal token count given a compute budget."""
    n_opt = optimal_params_for_compute(compute_flops)
    return 20.0 * n_opt


def benchmark_to_compute_estimate(
    swe_bench_score: float,
    reference_points: list[tuple[float, float]],
) -> float:
    """
    Log-linear fit: estimate compute FLOPs from SWE-bench score.
    reference_points: list of (flops, swe_bench_score) tuples.
    """
    if not HAS_NUMPY:
        # Simple manual log-linear interpolation
        log_flops = [math.log10(f) for f, _ in reference_points]
        scores = [s for _, s in reference_points]
        # Linear regression on log scale
        n = len(log_flops)
        mean_x = sum(log_flops) / n
        mean_y = sum(scores) / n
        slope = sum((log_flops[i] - mean_x) * (scores[i] - mean_y)
                    for i in range(n)) / sum((x - mean_x) ** 2 for x in log_flops)
        intercept = mean_y - slope * mean_x
        target_log_flops = (swe_bench_score - intercept) / slope
        return 10 ** target_log_flops

    log_flops = np.array([math.log10(f) for f, _ in reference_points])
    scores = np.array([s for _, s in reference_points])
    coeffs = np.polyfit(log_flops, scores, 1)
    target_log_flops = (swe_bench_score - coeffs[1]) / coeffs[0]
    return 10 ** target_log_flops


def main(plot: bool = False) -> None:
    # Build reference points from known models
    reference_points = [
        (m["flops"], m["swe_bench_verified"])
        for m in REFERENCE_MODELS.values()
        if m["flops"] is not None
    ]

    mythos_score = REFERENCE_MODELS["Claude Mythos (target)"]["swe_bench_verified"]
    estimated_flops = benchmark_to_compute_estimate(mythos_score, reference_points)
    estimated_params = optimal_params_for_compute(estimated_flops)
    estimated_tokens = optimal_tokens_for_compute(estimated_flops)

    print("=" * 60)
    print("MYTHOS COMPUTE BUDGET ESTIMATION")
    print("=" * 60)
    print(f"SWE-bench Verified target:   {mythos_score * 100:.1f}%")
    print(f"Estimated compute:           {estimated_flops:.2e} FLOPs")
    print(f"Chinchilla-optimal params:   {estimated_params / 1e12:.1f}T parameters")
    print(f"Chinchilla-optimal tokens:   {estimated_tokens / 1e12:.0f}T tokens")
    print()
    print("NOTE: These are log-linear extrapolations, not measurements.")
    print("SWE-bench may not scale perfectly with general compute.")

    results = {
        "method": "Chinchilla log-linear benchmark extrapolation",
        "target_swe_bench_score": mythos_score,
        "estimated_flops": estimated_flops,
        "estimated_params": estimated_params,
        "estimated_tokens": estimated_tokens,
        "confidence": "SPECULATIVE — extrapolation beyond reference range",
        "reference_models": {k: {kk: vv for kk, vv in v.items() if kk != "params"}
                             for k, v in REFERENCE_MODELS.items()},
    }

    import os
    os.makedirs("results", exist_ok=True)
    with open("results/scaling_law_fit.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\nResults saved to results/scaling_law_fit.json")

    if plot and HAS_NUMPY:
        fig, ax = plt.subplots(figsize=(10, 6))
        flops_list = [f for f, _ in reference_points]
        scores_list = [s for _, s in reference_points]
        names = [k for k, v in REFERENCE_MODELS.items() if v["flops"] is not None]

        ax.scatter(flops_list, scores_list, c="blue", zorder=5)
        for name, f, s in zip(names, flops_list, scores_list):
            ax.annotate(name, (f, s), textcoords="offset points", xytext=(5, 5))

        ax.scatter([estimated_flops], [mythos_score], c="red", s=200,
                   marker="*", zorder=6, label="Mythos (estimated)")
        ax.set_xscale("log")
        ax.set_xlabel("Training Compute (FLOPs)", fontsize=12)
        ax.set_ylabel("SWE-bench Verified Score", fontsize=12)
        ax.set_title("Scaling Law Fit: Compute vs. SWE-bench (Mythos Extrapolation)")
        ax.legend()
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig("results/scaling_law_fit.png", dpi=150)
        print("Plot saved to results/scaling_law_fit.png")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--plot", action="store_true",
                        help="Generate scaling law plot (requires matplotlib)")
    args = parser.parse_args()
    main(plot=args.plot)
