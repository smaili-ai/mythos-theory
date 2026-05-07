# 06 — Open Questions and Falsifiable Hypotheses Tracker

This document is a living registry of every hypothesis in this project and its
current status. Update this file whenever new public information arrives or an
experiment produces a result.

---

## Hypothesis Status Key

| Symbol | Meaning |
|--------|---------|
| ❓ | Open — no data yet |
| ✅ | Confirmed by experiment or public data |
| ❌ | Falsified by experiment or public data |
| ⚠️ | Partially supported — ambiguous result |
| 🔒 | Cannot be tested without Anthropic access |

---

## Architecture Hypotheses

| ID | Hypothesis | Status | Evidence | Experiment |
|----|-----------|--------|----------|------------|
| H-MoE-1 | Code/cyber-specialised expert cluster exists in Mythos | ❓ | BBBF-04 latency probe pending | MM-01, BBBF probe |
| H-ATT-1 | Periodic full + sliding-window attention (every K layers) | ❓ | Consistent with 1M context economics | Context ablation |
| H-POS-1 | Dynamic NTK RoPE on full-attention layers only | ❓ | — | RoPE scaling sweep |
| H-HYBRID | Mythos uses Mamba/SSM layers for long-context | ❓ | Low confidence; interpretability tension | MM-C experiment |
| H-PREC | FP8 inference precision at deployment | 🔒 | Unconfirmable without weights | — |

---

## Training Hypotheses

| ID | Hypothesis | Status | Evidence | Experiment |
|----|-----------|--------|----------|------------|
| H-DATA-1 | 5% high-quality cyber corpus drives SOTA cyber perf | ❓ | Consistent with P3 capability description | MM-03 sweep |
| H-CURR-1 | Mythos pretrained on private SWE-bench Pro distribution | ❓ | Explains 77–78% Pro score | Cannot test directly |
| H-CURR-2 | Sandbox escape was emergent, not trained directly | ❓ | Supported by P3 framing ("unexpected") | 🔒 |
| H-RLHF-1 | Automated scalar reward (test pass) for code + math | ❓ | Necessary at scale; Anthropic hints in P2 | MM-06 (CTI) |
| H-RT-1 | Hard-coded SFT guard against specific JIT heap spray pattern | 🔒 | Possible; unverifiable | — |
| H-CAI | Constitutional AI v3 with dynamic per-task constitutions | ❓ | Extrapolated from CAI v1/v2 public work | CTI experiment |

---

## Capability Constraints (from `01_capabilities_surface.md`)

| Constraint | Status | Verified By |
|------------|--------|-------------|
| C-1: Long-horizon file editing (1M context) | ✅ | P1, P2 (primary sources) |
| C-2: Latent reasoning robustness | ✅ | P2 §3.4 (thinking evaluation) |
| C-3: Persistent environment model | ✅ | P3 (sandbox escape proof) |
| C-4: Executable exploit code generation | ✅ | P3, P7 |
| C-5: No attention degradation at 1M tokens | ✅ | P2 (GraphWalks benchmark) |
| C-6: CoT paraphrase invariance | ✅ | P2 §3.4 |
| C-7: Multi-step tool-use / working memory | ✅ | P3 (5-step sandbox escape chain) |
| C-8: Strong constitutional alignment | ✅ | P2, P4 ("best aligned to date") |

---

## Open Research Questions

These are questions where no public data and no affordable experiment can provide
an answer. They are documented for future community investigation.

1. **What is the exact MoE router architecture?** Token-choice vs. expert-choice
   routing has large implications for load balancing. Public information does not
   distinguish.

2. **Does Mythos use speculative decoding at inference time?** The token efficiency
   claim in P2 could be explained by aggressive speculative decoding with a
   smaller draft model, not purely by architectural efficiency.

3. **What is the exact constitutional training signal for cybersecurity?** P2
   describes "cyber-specific safety rules" but does not enumerate them. Without
   this, CTI results are ambiguous.

4. **Is there a separate reasoning model / extended thinking mode?** The CoT
   paraphrase invariance result (C-6) is consistent with a hidden scratchpad stream
   (o1/o3 style). This would be a major architectural distinction.

5. **What is the KV cache strategy for 1M context?** Options include: ring
   attention, flash attention with chunked prefill, retrieval-augmented KV eviction,
   or a hierarchical cache. Each has different performance characteristics.

6. **How large is the alignment fine-tuning compute budget relative to pretraining?**
   P2 hints it is substantial but does not quantify. This matters for understanding
   whether RLHF or CAI is the dominant alignment signal.

---

## Update Log

| Date | Update | Source |
|------|--------|--------|
| 2026-05-07 | Initial document created | `docs/` synthesis |
| — | — | — |
