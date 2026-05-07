# 03 — Training Hypotheses

This document reconstructs the likely training pipeline for Mythos from Anthropic's
public risk reports (P2), scaling law literature, and observable behavioural deltas
between Claude model generations.

---

## 1. Training Pipeline Overview

Based on P2 and observable behaviour, we hypothesise the following 5-stage pipeline:

```
Stage 0: Data Curation
      ↓
Stage 1: Large-Scale Pretraining   (compute-optimal, ~10²⁴–10²⁵ FLOPs)
      ↓
Stage 2: Code + Cyber Specialisation  (curriculum fine-tuning)
      ↓
Stage 3: Supervised Fine-Tuning (SFT)  (instruction following, multi-turn)
      ↓
Stage 4: Constitutional AI + RLHF      (alignment + safety)
      ↓
Stage 5: Red-Team Guided Refinement    (cyber risk mitigation, Project Glasswing)
```

---

## 2. Stage 0: Data Curation

### 2.1 Hypothesised corpus composition

| Domain | Estimated % | Rationale |
|--------|-------------|-----------|
| Web text (deduplicated, quality-filtered) | ~40% | Foundation for language model |
| Code (GitHub, GitLab, Bitbucket) | ~25% | SWE-bench 93.9% requires massive code coverage |
| Scientific papers (arXiv, PubMed) | ~10% | GPQA Diamond / LAB-bench performance |
| Mathematics (ProofWiki, formal proofs, competition problems) | ~8% | USAMO-level performance |
| Security / CVE writeups, CTF solutions, exploit databases | ~5% | CyberGym / Cybench SOTA |
| Legal, financial, policy documents | ~5% | Glasswing enterprise use-cases |
| Multilingual | ~7% | General capability |

**Hypothesis H-DATA-1**: The 5% security corpus is disproportionately high quality
and structurally diverse, including:
- CVE writeups with working PoC code
- CTF solve scripts with annotated reasoning
- Formal vulnerability analyses from publications like *USENIX Security*, *CCS*

This domain-specific corpus density is the primary driver of cyber SOTA, not just
model scale.

### 2.2 Quality filtering

Anthropic has described progressive quality filtering in prior Claude generations.
We hypothesise Mythos uses a **classifier cascade**:
1. Perplexity-based deduplication (exact + near-duplicate removal).
2. Quality classifier trained on human preference data to score web text.
3. Domain-specific classifiers for code quality (syntactic validity, test pass rate).
4. **Novel [SPECULATIVE]**: An exploit-validity classifier that scores security
   writeups by whether the described technique is technically coherent — trained
   on a curated seed set of validated CVEs.

---

## 3. Stage 1: Pretraining

### 3.1 Compute budget estimate

Using the Chinchilla (Hoffmann et al., 2022) optimal scaling law:

```
N_opt ≈ 0.2 × C^0.5    (parameters)
D_opt ≈ 20 × N         (tokens)
```

For Mythos's capability profile (estimated C ≈ 10²⁴–10²⁵ FLOPs):
- N_opt ≈ 2T–10T parameters (consistent with S1 estimate of ~10T)
- D_opt ≈ 40T–200T tokens

However, Mythos's code + cyber specialisation suggests the effective token count in
those domains is *much higher* than the Chinchilla ratio prescribes — a "beyond
Chinchilla" regime where data quality and domain balance outperform raw token count
for specialised benchmarks.

Refer to `scripts/analysis/fit_scaling_laws.py` for a parameterised fit.

### 3.2 Infrastructure [SPECULATIVE]

Anthropic operates its own training infrastructure. For a 10T MoE model we estimate:
- ~4,000–16,000 H100/H200 GPUs in a pipeline+tensor parallel configuration.
- ZeRO Stage 3 or equivalent for optimizer state sharding.
- Mixed FP8 / BF16 training (expert activations in FP8, router/attention in BF16).

---

## 4. Stage 2: Code and Cyber Specialisation (Curriculum Fine-Tuning)

This is the most architecturally important stage and the one least covered in
public documentation. We hypothesise a **two-phase curriculum**:

### Phase A: Code Specialisation

- Dataset: Curated GitHub issues + pull requests with tests (SWE-bench-style).
- Objective: Standard next-token prediction but with a higher *code token weight* in
  the loss function.
- Duration: ~100B–500B code tokens.
- Key signal: Masked repo-wide file-edit tasks where the model must edit N files to
  make test suites pass.

**Hypothesis H-CURR-1**: Mythos was trained on a *private version* of SWE-bench Pro
problems with full repository context, not just the issue description. This would
directly explain the 77–78% Pro score — the model has "seen" the distribution.

### Phase B: Cyber Specialisation

- Dataset: Structured exploit writeups, CVE+PoC pairs, CTF solutions.
- Objective: Next-token prediction + **execution trace grounding**: the model
  predicts both the exploit code *and* the expected memory state after each step.
- Key signal: Bash-chain tasks run against containerised vulnerable environments
  (internal Anthropic cyber-range, analogous to our `cyber_gym_toy/`).

**Hypothesis H-CURR-2**: The sandbox escape capability (P3) was *emergent* from
this stage — Anthropic did not explicitly train for sandbox escape, but the
combination of memory-layout reasoning + exploit chaining generalised to that
capability.

---

## 5. Stage 3: Supervised Fine-Tuning (SFT)

Standard instruction-following SFT on multi-turn conversation data. Key differences
from Claude 3 generation:

- Tool-use formats are more deeply integrated — the SFT data likely includes
  *interleaved* tool calls and reasoning traces rather than separate phases.
- Long-document SFT: training examples that require reading a 500K-token codebase
  before answering.

---

## 6. Stage 4: Constitutional AI + RLHF

### 6.1 Constitutional AI (CAI) v3

Anthropic's Constitutional AI v1 (2022) specified a static set of principles.
By Mythos, we hypothesise a **CAI v3** approach:

1. **Dynamic constitutions**: The model is given a per-task constitution that
   includes domain-specific safety rules (e.g., for cybersecurity tasks: "do not
   generate attacks against production systems").
2. **Self-critique loops**: The model scores its own outputs against the
   constitution before finalising, trained via a multi-turn self-play procedure.
3. **Adversarial constitution red-teaming**: During RL, some constitutions are
   adversarially perturbed to test robustness.

### 6.2 Constitutional Trace Inversion (CTI) — Novel Method

**CTI** is our original reverse-engineering technique for constitutional training:

1. Sample identical prompts from the Claude 3.5 Opus API and a Mythos-equivalent.
2. Compute the KL divergence of the token distributions: KL(Mythos || Opus).
3. High-KL token positions indicate where the constitutional fine-tuning *changed*
   the output distribution most strongly.
4. Cluster these positions by semantic category (refusal tokens, hedging tokens,
   reasoning tokens).
5. The cluster structure reveals the likely *axes* of the constitutional training
   signal.

See `notebooks/03_alignment_behavior.ipynb` for the first CTI experiment.

### 6.3 RLHF at Scale

The reward model for Mythos RLHF must be able to evaluate:
- Multi-file code correctness (requires running tests, not just human preference).
- Mathematical proof validity (requires formal verification or expert labellers).
- Exploit completeness (requires executing against a cyber range).

**Hypothesis H-RLHF-1**: Mythos uses **automated scalar reward** for code (test
pass rate) and math (symbolic verifier), supplemented by human preference labelling
only for open-ended reasoning tasks. This is necessary because human labellers
cannot evaluate Olympiad math or novel exploits at training scale.

---

## 7. Stage 5: Red-Team Guided Refinement

P2 describes an extensive red-team program run jointly with Glasswing partners.
Key inferred properties:

- Glasswing partners (CrowdStrike, NVIDIA, etc.) provided real vulnerability
  triage tasks as evaluation sets.
- Any case where Mythos produced a higher-severity output than expected was used
  as a negative training signal.
- The sandbox escape case (P3) was discovered *during red-teaming* and led to a
  targeted fine-tuning run to constrain autonomous escape-capable behaviour.

**Hypothesis H-RT-1**: Mythos has a *hard-coded behavioural guard* against
generating JIT heap spray payloads targeting production browser engines, inserted
via direct SFT on the specific exploit pattern. This is more robust than a
constitutional rule for this specific capability.
