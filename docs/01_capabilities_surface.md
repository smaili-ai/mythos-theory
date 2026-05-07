# 01 — Capabilities Surface Reconstruction

This document aggregates empirical constraints from public benchmark data and risk
reports. Any architectural hypothesis must be consistent with **all** constraints
here. Sources are tagged P1–P7 / S1–S4 per `00_background.md`.

---

## 1. Quantitative Benchmark Constraints

### 1.1 Coding

| Benchmark | Score | Delta vs. Opus 3.5 | Source |
|-----------|-------|--------------------|--------|
| SWE-bench Verified | **93.9 %** | +~34 pp | P1, S3 |
| SWE-bench Pro | **~77–78 %** | +~30 pp (est.) | P1 |
| SWE-bench Multimodal | SOTA (exact TBD) | — | P1 |

**Constraint C-1**: Architecture must support *long-horizon file-editing plans*
spanning hundreds of function calls. Single-step code generation is insufficient;
the model must maintain state across a multi-file repository within one context
pass.

### 1.2 Mathematics and Science

| Benchmark | Score | Source |
|-----------|-------|--------|
| USAMO / Olympiad-level math | **SOTA** | P1, P2 |
| GPQA Diamond | **SOTA** | P1 |
| LAB-bench (biology) | SOTA | P2 |

**Constraint C-2**: Internal reasoning chains must be long, self-correcting, and
robust to paraphrase (see §3 below). Pure next-token prediction on surface tokens
is insufficient — the latent space must encode symbolic structure.

### 1.3 Cybersecurity

| Benchmark | Result | Source |
|-----------|--------|--------|
| Cybench | **SOTA** | P1, P2 |
| CyberGym | **SOTA** | P1, P3 |
| Autonomous zero-day discovery | **Thousands** (controlled) | P3, P7 |
| Sandbox escape (confirmed) | **1 full chain** | P3, P5 |

**Constraint C-3**: The model must maintain a precise, updatable *mental model* of a
running system (file system state, process list, memory layout, network stack) across
tens of thousands of tokens.

**Constraint C-4**: The model must generate *executable*, syntactically correct
exploit code, not just descriptions.

### 1.4 Context and Efficiency

| Property | Value | Source |
|----------|-------|--------|
| Context window | **1,048,576 tokens** (1M) | P1, P2 |
| Long-context degradation | Substantially lower than Opus | P2 |
| Token efficiency vs. Opus | "Substantially more efficient" | P2 |

**Constraint C-5**: No "lost in the middle" degradation at 1M tokens. Positional
encoding and attention patterns must maintain retrieval fidelity across the full
window.

---

## 2. Qualitative Engineering Constraints

Derived from the quantitative constraints above plus qualitative language in P2:

### C-6: Robust Latent Reasoning

Anthropic's "thinking evaluation" (P2 §3.4) shows that Mythos performance on hard
math is *stable even when CoT text is paraphrased* by an intermediary model. This
means:
- Reasoning is encoded in **latent activations**, not in CoT surface tokens.
- Training must have included explicit CoT robustness objectives or a training
  distribution where paraphrased CoT was common.

### C-7: Tool-Use and Environment Simulation

CyberGym scores imply the model can:
- Issue bash commands, read outputs, and update a persistent mental model.
- Plan multi-step exploit chains where step N depends on the output of step N-1.

This is qualitatively harder than standard instruction following; it requires
something analogous to a *working memory* over very long token distances.

### C-8: Minimal Regression on Alignment

P2 and P4 both note that Mythos is "best aligned so far" despite elevated capability.
This constrains training: alignment must have been substantially reinforced, not
traded off against capability, implying a large RLHF / Constitutional AI budget on
top of pretraining.

---

## 3. Thinking Evaluation — Deep Dive

Source: P2 §3.4 ("Reasoning Robustness Evaluation").

Anthropic ran the following experiment (paraphrased from public risk report):

1. Mythos solves a hard math problem and produces a CoT trace.
2. A second model (Claude 3 Sonnet) *paraphrases* the CoT trace — same logical
   steps, different surface tokens.
3. Mythos is given the paraphrased CoT as a prefix and asked to complete the answer.
4. **Finding**: Answer accuracy degrades by < 2 pp.

**Implication for reverse engineering**:
This implies Mythos compresses CoT into a *high-dimensional, semantically invariant
latent state*. The model likely uses **extended thinking tokens** (possibly
a separate "reasoning scratchpad" decoding stream analogous to o1/o3) that are
trained to be paraphrase-invariant.

Hypothesised mechanism: internal KV cache entries for reasoning tokens are pooled
into a fixed-size summary vector before being written to the next attention layer.
This is consistent with:
- Hymba's *learnable meta-tokens* (prepended cache state).
- DeepSeek V3's *auxiliary reasoning heads*.

---

## 4. Derived Constraint Matrix

| Constraint | Architectural Implication | Falsification Condition |
|------------|--------------------------|------------------------|
| C-1 | ≥ 1M context, low degradation | Accuracy drop > 5% at 512K tokens |
| C-2 | Robust latent reasoning | CoT paraphrase drops > 5% on Olympiad tasks |
| C-3 | Persistent state across 50K+ tokens | State tracking fails on long-horizon CTF |
| C-4 | Code-specialised expert(s) in MoE | No expert activation cluster for code tokens |
| C-5 | Sub-quadratic attention or hierarchical KV | Memory footprint incompatible with 1M context on known hardware |
| C-6 | CoT paraphrase invariance | — (already tested by P2) |
| C-7 | Working memory / tool-use scaffolding | Fails on 10-step bash-chain tasks |
| C-8 | Strong Constitutional AI fine-tuning | Refusal rate significantly below Claude 3.5 Opus |

The constraint matrix is updated as new public information arrives.
See `06_open_questions.md` for currently open falsification tests.
