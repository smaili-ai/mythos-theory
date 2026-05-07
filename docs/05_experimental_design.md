# 05 — Experimental Design: Mini-Mythos

This document specifies the concrete experimental programme for building, training,
and evaluating smaller open models whose performance provides evidence for or
against the hypotheses in documents 02 and 03.

---

## 1. Experimental Goals

Mini-Mythos is **not** an attempt to clone Mythos. It is a scientific instrument
for hypothesis testing. Each experiment tests one or more hypotheses from the
constraint matrix.

| Experiment | Hypothesis Tested | Expected Outcome if Correct |
|------------|------------------|------------------------------|
| MM-01: MoE vs Dense ablation | H-MoE-1 | MoE outperforms dense by > 5pp on code benchmark at same active param count |
| MM-02: Context window ablation | C-5, C-7 | Accuracy on chain-depth CTF drops sharply below 256K tokens |
| MM-03: Cyber corpus proportion sweep | H-DATA-1 | Peak cyber benchmark accuracy at ~5–8% cyber data, not maximum |
| MM-04: CoT robustness training | C-6, H-CURR-1 | CoT paraphrase invariance improves with explicit robustness training |
| MM-05: ASRPM feature geometry | H-MoE-1 | Code/cyber features are linearly separable in MoE, entangled in dense |
| MM-06: CTI constitutional delta | H-RLHF-1 | Constitutional fine-tuning KL spike concentrated on refusal/hedge tokens |

---

## 2. Model Specifications

### 2.1 MM-A: "Mini-Mythos Core" (primary experiment vehicle)

```yaml
model_name:   mini_mythos_core
arch:         transformer_moe
total_params: 7B
active_params: 1.5B per token
config:
  n_layers: 32
  d_model: 4096
  n_heads: 32
  d_ff: 16384
  moe:
    n_experts: 64
    top_k: 2
    capacity_factor: 1.25
    router_type: load_balanced
  attention:
    type: grouped_query
    kv_groups: 8
  context_window: 131072   # 128K — scaled down from 1M
  rope_scaling:
    type: dynamic_ntk
    factor: 4.0
  precision:
    training: bfloat16
    inference: fp8
```

This is the canonical Mini-Mythos configuration. All ablations are measured as
deltas from this baseline.

### 2.2 MM-B: "Dense Baseline" (MM-01 ablation)

Same parameter budget, but no MoE — all FFN parameters active per token:

```yaml
model_name:   mini_mythos_dense_baseline
arch:         transformer_dense
total_params: 1.5B    # same active compute as MM-A
config:
  n_layers: 32
  d_model: 2048
  n_heads: 16
  d_ff: 8192
  # No MoE
  context_window: 131072
```

### 2.3 MM-C: "Hymba Hybrid" (long-context efficiency test)

```yaml
model_name:   mini_mythos_hymba
arch:         transformer_mamba_hybrid
total_params: 1.5B
config:
  n_layers: 32
  hybrid_schedule:
    attention_layers: [0, 4, 8, 12, 16, 20, 24, 28, 31]  # every 4th layer
    mamba_layers: remaining
  attention:
    type: sliding_window
    window_size: 4096
  meta_tokens: 16    # learnable prepended cache tokens
  context_window: 524288   # 512K — tests Hymba's long-context claim
```

---

## 3. Training Dataset

| Source | Size | Domain |
|--------|------|--------|
| The Stack v2 (filtered) | 300B tokens | Code (Python, C, C++, Rust, Go) |
| OpenMathInstruct-2 | 14B tokens | Math (competition + step-by-step) |
| Open-Platypus + LIMA | 2B tokens | Instruction following |
| CTF Archive (public writeups) | 3B tokens | Cybersecurity / exploit reasoning |
| FineWeb-Edu | 150B tokens | High-quality web text |
| arXiv CS+Math (2000–2025) | 30B tokens | Technical reasoning |
| **Total** | **~500B tokens** | — |

**Rationale**: 500B tokens is roughly compute-optimal for a 7B MoE model at our
target GPU budget (~32 H100s for 2 weeks). The cyber corpus is ~0.6% of total,
but is highest quality and includes detailed reasoning traces.

---

## 4. Training Procedure

### 4.1 Pretraining (Stage 1)

```bash
python models/training/train_mini_mythos.py \
  --config models/configs/mini_mythos_core.yaml \
  --dataset data/processed/pretrain_mix.jsonl \
  --max_tokens 500_000_000_000 \
  --lr 3e-4 \
  --warmup_steps 2000 \
  --cosine_decay_to 3e-5 \
  --batch_size 2048 \
  --sequence_length 32768 \
  --gradient_checkpointing
```

### 4.2 Code + Cyber Specialisation (Stage 2)

```bash
python models/training/train_mini_mythos.py \
  --config models/configs/mini_mythos_core.yaml \
  --resume_from checkpoints/pretrain_final.pt \
  --dataset data/processed/specialisation_mix.jsonl \
  --max_tokens 20_000_000_000 \
  --lr 1e-4 \
  --domain_weights code:0.5,cyber:0.3,math:0.2
```

### 4.3 SFT + Constitutional Alignment (Stages 3–4)

Uses standard instruction tuning on open SFT datasets followed by DPO
(Direct Preference Optimisation) as a Constitutional AI proxy:

```bash
# SFT
python models/training/sft.py \
  --base checkpoints/specialisation_final.pt \
  --dataset data/processed/sft_mix.jsonl

# DPO (Constitutional)
python models/training/dpo.py \
  --base checkpoints/sft_final.pt \
  --preference_data data/processed/constitutional_pairs.jsonl \
  --beta 0.1
```

---

## 5. Evaluation Schedule

After each training stage, run:

```bash
# Core benchmarks
python evals/run_evals.py \
  --model checkpoints/stage_{N}_final.pt \
  --tasks swe_bench_lite,math_olympiad,cyber_ctf_toy,alignment_probes \
  --output results/stage_{N}_evals.json
```

Results are compared against the constraint matrix in `01_capabilities_surface.md`.
Any Mini-Mythos checkpoint that violates a constraint eliminates the corresponding
architecture hypothesis.

---

## 6. Infrastructure Requirements

| Resource | Specification | Estimated Cost |
|----------|--------------|----------------|
| GPUs | 32× H100 80GB (or equivalent) | ~$15K–$25K (cloud, 2 weeks) |
| Storage | 10TB NVMe (dataset + checkpoints) | ~$200/month |
| CPU nodes | 8× 64-core (data preprocessing) | ~$500 (one-time) |
| Network | 800Gb/s InfiniBand (for tensor parallel) | Included in GPU cluster |

Budget-constrained alternative: Use 8× A100 40GB with gradient checkpointing and
sequence packing. Training time ~6 weeks instead of 2.
