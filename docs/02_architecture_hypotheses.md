# 02 — Architecture Hypotheses

This document derives and scores candidate architectures against the constraint
matrix in `01_capabilities_surface.md`. All claims labelled [SPECULATIVE] are
inferences, not confirmed facts.

---

## 1. Methodology: Black-Box Behavioral Fingerprinting (BBBF)

**BBBF** is our original contribution. Rather than guessing architecture from
parameter counts alone, we use a structured prompt protocol on publicly available
Claude API models to *infer likely architectural properties of Mythos by observing
scaling deltas*.

### 1.1 Protocol

For each probe type, we:
1. Run the probe on Claude 3.5 Sonnet, Claude 3 Opus, and (if accessible) any
   Mythos-equivalent.
2. Record the metric (accuracy, latency, token count, error type).
3. Fit a scaling curve and extrapolate to the Mythos benchmark data points.
4. Use the extrapolation to constrain architectural parameters.

See `scripts/analysis/bbbf_probe.py` for implementation.

### 1.2 Probe Battery

| Probe ID | Stimulus | Metric | Target Constraint |
|----------|----------|--------|------------------|
| BBBF-01 | Needle-in-haystack at 4K, 16K, 64K, 200K tokens | Recall accuracy | Attention decay rate → infer RoPE scale |
| BBBF-02 | Multi-file code edit spanning N files | Success rate vs. N | Long-horizon coding capacity |
| BBBF-03 | CoT paraphrase stability (replicate P2 experiment) | Accuracy delta | Latent reasoning robustness |
| BBBF-04 | Domain-switching mid-prompt (code → math → cyber) | Latency spike | MoE routing overhead signal |
| BBBF-05 | Repeated token flooding (n=10K identical tokens) | Perplexity / coherence | Attention pattern shape |
| BBBF-06 | Bash-chain task of depth D | Success rate vs. D | Working memory capacity |

BBBF-04 is particularly novel: if Mythos uses MoE, switching between expert domains
mid-prompt should produce a *measurable latency spike* as routers reconfigure. In a
dense model, no such spike exists. This gives us a probabilistic MoE detector via
API timing alone.

---

## 2. Baseline Assumption: Sparse MoE at ~10T Parameters

Multiple independent secondary analyses (S1, S2) converge on a ~10T total parameter
count. We treat this as [SPECULATIVE] but use it as the anchor for our hypothesis
space.

**Reasoning**:
- Chinchilla-optimal compute for a model achieving Mythos's benchmark profile
  (estimated from scaling law fits in `fit_scaling_laws.py`) requires ~10²⁴–10²⁵
  FLOPs.
- At reasonable training token counts (5–20T tokens), this implies a model of
  roughly 10T parameters.
- Hardware constraints (H100/H200 cluster sizes known to Anthropic) make a 10T dense
  model economically implausible for inference. A sparse MoE with ~10% active
  parameters per token (→ 1T active params) is far more viable.

---

## 3. Primary Hypothesis: `mythos_moe_hypothesis`

```
Total params:    ~10T  [SPECULATIVE]
Active params:   ~0.8–1.2T per token
Architecture:    Transformer-based sparse MoE
```

### 3.1 Layer Dimensions

| Hyperparameter | Hypothesised Value | Rationale |
|----------------|-------------------|-----------|
| `n_layers` | 120 | Depth needed for multi-step logical routing; consistent with Anthropic's interpretability work showing many composed features |
| `d_model` | 16384 | Wide residual stream for rich multi-domain knowledge; consistent with MoE where FFN weight lives in experts |
| `n_heads` | 128 | Granular attention distribution across 1M token window |
| `d_ff` | 65536 | Standard 4× expansion split across experts |
| `d_head` | 128 | (`d_model` / `n_heads`) |

### 3.2 MoE Configuration

| Hyperparameter | Hypothesised Value | Rationale |
|----------------|-------------------|-----------|
| `n_experts` | 256 | Domain specialisation: code, cyber, math, language, reasoning each likely have dedicated expert clusters |
| `top_k` | 4 | Balances compute (4 × expert cost) vs. sparsity; token-choice routing |
| `capacity_factor` | 1.25 | Buffer for load imbalance, especially for long-context code tokens |
| `router_type` | `load_balanced` | Auxiliary load-balancing loss prevents expert collapse (standard since GShard) |

**Hypothesis H-MoE-1** [SPECULATIVE]: At least one expert cluster is *exclusively*
activated by code/exploit tokens. This would explain why Mythos's SWE-bench score
jumps discontinuously rather than smoothly — the expert was trained with a
large code-specialised corpus during pretraining.

### 3.3 Attention Mechanism

| Property | Hypothesised Value | Rationale |
|----------|--------------------|-----------|
| `attention_type` | Grouped-Query Attention (GQA) | KV cache for 1M context at 120 layers is prohibitive without GQA |
| `kv_groups` | 16 | Reduces KV cache ~8× vs. MHA; balance of efficiency and quality |
| Local+global | Likely sliding-window + full-attention hyper-layers | "Lost in the middle" suppression requires some full-attention layers at regular intervals |

**Hypothesis H-ATT-1** [SPECULATIVE]: Mythos uses a periodic attention pattern:
every K layers use full causal attention; intermediate layers use sliding-window
with window size ~4096 tokens. This is consistent with LongFormer/BigBird strategies
and is the most computationally tractable way to handle 1M tokens.

### 3.4 Positional Encoding

| Property | Hypothesised Value | Rationale |
|----------|--------------------|-----------|
| `pos_enc` | RoPE | Standard Anthropic family; confirmed in Claude 3 model card |
| `rope_scaling` | Dynamic NTK | Enables extrapolation to 1M without retraining from scratch |
| `rope_base` | 500,000 | Extended base frequency for long-document retrieval |
| `rope_factor` | 8.0 | Long-context fine-tuning factor |

**Hypothesis H-POS-1**: Dynamic NTK-aware RoPE is applied only to full-attention
hyper-layers; sliding-window layers use unscaled RoPE since their effective context
is bounded by the window.

### 3.5 Precision

| Stage | Format |
|-------|--------|
| Pretraining | BF16 |
| Fine-tuning | BF16 |
| Inference | FP8 (highly likely for Glasswing deployment efficiency) |

---

## 4. Alternative Hypothesis: Hybrid Transformer–Mamba

Inspired by NVIDIA's **Hymba** architecture (2025), a plausible alternative is that
Mythos interleaves standard attention layers with SSM (Mamba/H3) layers:

- **Pro**: 11× smaller KV cache, 3.5× faster inference throughput — critical for 1M
  context inference at scale.
- **Con**: Anthropic's interpretability work (Scaling Monosemanticity, transformer-
  circuits) assumes standard transformer residual streams. A Mamba hybrid would
  complicate SAE-based interpretability.
- **Assessment**: [SPECULATIVE, low-medium confidence]. Possible for specific layers
  (e.g., long-context summarisation layers), but unlikely to replace full attention.

See `models/configs/hymba_hybrid.yaml` for the Mini-Mythos experimental version.

---

## 5. Hypothesis Scoring Matrix

| Hypothesis | Constraint Satisfied | Constraint Violated | Confidence |
|------------|---------------------|---------------------|------------|
| H-MoE-1 (code-specialist experts) | C-1, C-4 | None from public data | Medium |
| H-ATT-1 (periodic full+sliding attention) | C-5 | None from public data | Medium-High |
| H-POS-1 (dynamic NTK for full-attn layers only) | C-5 | None from public data | Medium |
| Hybrid Mamba | C-5 | C-6 (interpretability constraint) | Low-Medium |

---

## 6. Activation-Space Reconstruction via Proxy Models (ASRPM)

We train smaller open models on Mythos benchmark tasks and extract their internal
activations using sparse autoencoders (SAEs), following Anthropic's own
*Scaling Monosemanticity* methodology. The resulting feature geometry serves as a
**lower-bound proxy** for Mythos's internal representation:

1. Train a 7B MoE model ("Mini-Mythos") on code + math + CTF corpora.
2. Apply a SAE with latent dim 16× hidden dim to each residual stream layer.
3. Extract monosemantic feature directions for concepts like `null_deref`,
   `heap_overflow`, `integer_overflow`, `format_string`.
4. Measure whether these features are **linearly separable** (consistent with a
   clean MoE where each expert specialises) or **entangled** (consistent with a
   dense model).

The geometry of the Mini-Mythos feature space gives us a falsifiable prediction for
what Anthropic's own SAE analysis of Mythos would likely look like.

See `notebooks/02_architecture_search.ipynb` for the first ASRPM experiment.
