# Contributing to Mythos Reverse Engineering

Thank you for your interest in contributing. This project is a scientific
research effort and has strict ethical requirements.

## Before You Contribute

By submitting a pull request you confirm:

1. **No proprietary material**: Your contribution contains no Anthropic code,
   weights, internal documentation, or leaked information of any kind.
2. **No Kye Gomez material**: No content authored by Kye Gomez is included.
3. **No real exploits**: Cyber evaluation tasks must be synthetic CTF-style only.
   No CVEs against production software. No working JIT heap spray payloads.
   No kernel exploit payloads.
4. **Sources cited**: Every factual claim traces to a P-tier source from
   `docs/00_background.md`. Speculative claims are tagged `[SPECULATIVE]`.
5. **Hypothesis-linked**: New experiments are linked to a hypothesis in
   `docs/06_open_questions.md`.

## Contribution Types

| Type | Accepted | Notes |
|------|----------|-------|
| New primary source analysis | Yes | Must be a public, unauthenticated URL |
| New architecture hypothesis | Yes | Must state falsification condition |
| New training recipe | Yes | Open datasets only |
| New synthetic CTF task | Yes | Must be self-contained with no real target |
| Benchmark result update | Yes | Must cite primary source |
| Real exploit code | **No** | Hard reject |
| Leaked model info | **No** | Hard reject |

## Code Style

- Python 3.11+
- Type annotations on all function signatures
- `ruff` for linting: `pip install ruff && ruff check .`
- `pytest` for tests: `pip install pytest && pytest tests/`

## Pull Request Process

1. Fork and create a feature branch.
2. Update `docs/06_open_questions.md` with any hypothesis status changes.
3. Run `python evals/run_evals.py --dry_run` to validate configs.
4. Open PR with description linking the hypothesis being tested.
