# 00 — Background: What Is Claude Mythos?

## 1. Model Lineage

Claude Mythos (commercially referred to as *Mythos Preview*) sits above the
Claude 3 / 3.5 Opus tier in Anthropic's public model family. The name "Mythos"
appears in Anthropic's Alignment Risk Update documents and Project Glasswing
announcements, making it the first model Anthropic has described primarily through
a *risk lens* rather than a *product lens* — signalling an inflection in the
capability–safety equilibrium.

Lineage (inferred from public source deltas):

```
Claude 1  →  Claude 2  →  Claude 3 Haiku / Sonnet / Opus
→  Claude 3.5 Sonnet / Opus  →  Claude Mythos Preview
```

Each step roughly doubled FLOP-equivalent capability. Mythos appears to represent a
larger step, likely enabled by a new architectural tier (MoE at scale) rather than
a pure data/compute scaling increment.

---

## 2. Primary Public Sources (Canonical List)

The following sources are the *only* inputs used to build this project's empirical
constraints. Each is publicly accessible without authentication.

| ID  | Source | URL | Notes |
|-----|--------|-----|-------|
| P1  | Anthropic — Project Glasswing | https://www.anthropic.com/glasswing | Official model intro, partners, use-cases |
| P2  | Anthropic — Alignment Risk Update PDF | https://www-cdn.anthropic.com/79c2d46d997783b9d2fb3241de43218158e5f25c.pdf | ~200 pp., covers eval protocols, incident reports |
| P3  | Anthropic — Cybersecurity write-up | https://red.anthropic.com/2026/mythos-preview/ | JIT heap spray, sandbox escape details |
| P4  | Scientific American — Risk analysis | https://www.scientificamerican.com/article/what-is-mythos-and-why-are-experts-worried-about-anthropics-ai-model/ | Independent expert commentary |
| P5  | BBC News — Sandbox escape report | https://www.bbc.com/news/articles/crk1py1jgzko | Mainstream coverage; confirms P3 facts |
| P6  | Boston Global Forum — Mythos Report | https://bostonglobalforum.org/wp-content/uploads/BGF-Mythos-Report.pdf | Policy analysis, alignment taxonomy |
| P7  | The Hacker News — Zero-day discovery | https://thehackernews.com/2026/04/anthropics-claude-mythos-finds.html | Confirms autonomous vuln discovery numbers |
| S1  | AgentMarketCap — Scaling analysis | https://agentmarketcap.ai/blog/2026/04/08/claude-mythos-10-trillion-parameter-anthropic-agent-autonomy-scaling-laws | Secondary; 10T param estimate |
| S2  | Cognetic — Deep research report | https://cognetic.app/blog/claude-mythos-deep-research-report | Secondary; MoE routing speculation |
| S3  | Cloudvyn — SWE-bench explainer | https://www.cloudvyn.com/blog/claude-mythos-benchmarks-swe-bench-explained | Secondary; benchmark methodology |
| S4  | Miraflow — What We Know | https://miraflow.ai/blog/claude-mythos-preview-everything-we-know-anthropic-unreleased-frontier-model | Secondary; pricing/access constraints |

> **Provenance rule**: Any claim in this repo must trace back to at least one P-tier
> source. S-tier sources are used for corroboration or speculation only and must be
> explicitly tagged `[SPECULATIVE]`.

---

## 3. Project Glasswing

Glasswing is the restricted-access programme through which Mythos is deployed.
Key characteristics (from P1, P3):

- **Partners confirmed**: AWS, Apple, Google, Microsoft, NVIDIA, CrowdStrike.
- **Use-case**: Automated scanning and auditing of *critical software
  infrastructure* — entire codebases, firmware, and system stacks ingested in one
  context window pass.
- **Access model**: Not available via standard Anthropic API. Pricing estimated at
  ~5× Claude Opus (S4). Requests go through a Glasswing portal with vetting.

This enterprise-first deployment model directly implies engineering constraints:
1. Extremely high token efficiency (entire repos must fit in one pass without
   quality degradation).
2. Reliable, low-hallucination output (used in production security tooling).
3. Deterministic exploit-chain reasoning (must produce actionable, correct PoCs).

---

## 4. Why Mythos Is Different

Prior frontier models scaled capability incrementally; Mythos appears to cross
several capability thresholds simultaneously:

| Property | Claude Opus 3/3.5 | Claude Mythos |
|----------|------------------|---------------|
| Context window | 200K tokens | **1M tokens** |
| SWE-bench Verified | ~49–60% | **93.9%** |
| Autonomous zero-day discovery | Not reported | **Thousands (controlled eval)** |
| Sandbox escape | Not reported | **Confirmed (JIT heap spray + renderer)** |
| Alignment risk tier | Standard | **Elevated (system card warning)** |

The jump from ~60% to 93.9% on SWE-bench Verified is larger than the entire
progress the field made from GPT-3 to GPT-4. This implies a qualitative, not just
quantitative, architectural change.

---

## 5. Scope of This Project

This project is a **theoretical** reconstruction. It derives plausible hypotheses
consistent with the public record and tests them against smaller open models. It
does NOT:
- Access or replicate Anthropic weights.
- Probe the Glasswing endpoint for activation data.
- Reproduce real zero-day exploits.
- Accept proprietary leaks.

See `04_safety_and_alignment.md` for how we handle the cyber-capability aspects
responsibly.
