# Mythos Reverse Engineering — Ground-Up Reconstruction

> **Ethical Disclaimer**: This repository operates exclusively on publicly
> available information. It does not contain, attempt to obtain, or reverse
> engineer Anthropic's proprietary weights, activations, or restricted code.
> Cyber evaluations are synthetic/CTF-only. 

---

## Why This Repository Exists

Claude Mythos (a.k.a. *Mythos Preview*) is Anthropic's highest-capability model to
date — deployed exclusively via **Project Glasswing** to partners such as AWS,
Apple, Google, Microsoft, NVIDIA, and CrowdStrike for critical software
infrastructure auditing. Its public benchmark profile is extraordinary:

| Domain    | Benchmark          | Reported Score |
|-----------|--------------------|----------------|
| Coding    | SWE-bench Verified | **93.9 %**     |
| Coding    | SWE-bench Pro      | **~77–78 %**   |
| Math      | USAMO / Olympiad   | **SOTA**       |
| Reasoning | GPQA Diamond       | **SOTA**       |
| Cyber     | Cybench / CyberGym | **SOTA**       |

These numbers, combined with a **1 M-token context window**, position Mythos as the
first publicly described model where the capability gap to prior frontier systems is
large enough to demand a new explanatory theory — not just a "bigger Opus".

This repository provides that theory, built from first principles.

---

## What Is Novel Here

Most prior coverage is speculation or paraphrase. **This project introduces four
original methodological contributions**:

1. **Black-Box Behavioral Fingerprinting (BBBF)** — a systematic prompt-based
   protocol for inferring internal architectural properties (attention span,
   expert routing patterns, CoT robustness) without model access.

2. **Activation-Space Reconstruction via Proxy Models (ASRPM)** — training
   smaller open models on the same tasks and using their internal representations
   as a lower-bound proxy for Mythos's feature geometry.

3. **Constitutional Trace Inversion (CTI)** — analysing the *delta* between
   Mythos's output distribution and that of Claude 3 Opus to reconstruct the likely
   constitutional fine-tuning signal.

4. **Cyber Capability Causal Graph** — a formal causal model linking architectural
   decisions (MoE routing, context window, CoT depth) to the observed cyber exploit
   chain metrics, enabling principled falsification.

---

## Repository Structure

```
mythos-re/
├── README.md                        ← this file
├── LICENSE
├── CONTRIBUTING.md
│
├── docs/
│   ├── 00_background.md             ← What Mythos is, primary sources
│   ├── 01_capabilities_surface.md   ← Empirical constraints from benchmarks
│   ├── 02_architecture_hypotheses.md← BBBF results → architecture constraints
│   ├── 03_training_hypotheses.md    ← Pretraining → RLHF → Constitutional AI
│   ├── 04_safety_and_alignment.md   ← Sandbox escape, alignment paradox
│   ├── 05_experimental_design.md    ← Mini-Mythos build plan
│   └── 06_open_questions.md         ← Falsifiable hypotheses tracker
│
├── data/
│   ├── raw/
│   │   ├── anthropic/               ← Downloaded public docs (PDFs, HTML)
│   │   ├── media_reports/
│   │   └── third_party_analyses/
│   └── processed/
│       ├── benchmarks.csv
│       ├── capabilities_summary.json
│       └── citations_index.json
│
├── scripts/
│   ├── scrape/
│   │   ├── download_anthropic_docs.py
│   │   └── ingest_web_sources.py
│   ├── parse/
│   │   ├── extract_benchmarks.py
│   │   └── extract_capabilities.py
│   └── analysis/
│       ├── fit_scaling_laws.py          ← Chinchilla fit for Mythos budget
│       ├── moe_capacity_sweep.py        ← Expert count vs. benchmark correlation
│       ├── context_window_simulation.py ← Attention degradation modelling
│       └── bbbf_probe.py               ← Black-Box Behavioral Fingerprinting
│
├── models/
│   ├── configs/
│   │   ├── mythos_moe_hypothesis.yaml   ← Primary MoE candidate
│   │   ├── mythos_dense_baseline.yaml   ← Dense upper-bound baseline
│   │   ├── zaya1_moe.yaml               ← ZAYA1-inspired small experiment
│   │   └── hymba_hybrid.yaml            ← Hymba hybrid Transformer+Mamba
│   └── training/
│       ├── train_mini_mythos.py
│       └── tasks/
│           ├── swe_bench_lite/
│           └── cyber_gym_toy/
│
├── evals/
│   ├── swe_bench_like/
│   ├── math_olympiad_like/
│   ├── cyber_like/
│   └── alignment/
│
└── notebooks/
    ├── 01_benchmark_landscape.ipynb
    ├── 02_architecture_search.ipynb
    └── 03_alignment_behavior.ipynb
```

---

## Quick Start

```bash
# 1. Clone and install
git clone https://github.com/your-org/mythos-re.git
cd mythos-re
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Ingest public primary sources
python scripts/scrape/download_anthropic_docs.py

# 3. Build capabilities surface
python scripts/parse/extract_benchmarks.py

# 4. Run Black-Box Behavioral Fingerprinting probes (requires any public LLM API)
python scripts/analysis/bbbf_probe.py --model claude-3-5-sonnet-20241022

# 5. Fit scaling laws against hypothesised Mythos compute budget
python scripts/analysis/fit_scaling_laws.py

# 6. Launch Mini-Mythos training (GPU required, ~7B MoE, 128K context)
python models/training/train_mini_mythos.py --config models/configs/zaya1_moe.yaml
```

---

## Ethics and Legal

- All sources used are public, unauthenticated, and non-proprietary.
- No attempt is made to probe, exfiltrate, or reproduce Anthropic model weights.
- Cyber evaluations run only against isolated, synthetic CTF-style environments.
- The project complies with Anthropic's public Terms of Service regarding the Claude
  API (black-box API calls only, within rate limits, no automated bulk extraction).
- See `CONTRIBUTING.md` for contributor code of conduct.
