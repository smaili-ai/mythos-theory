#!/usr/bin/env python3
"""
extract_benchmarks.py — Parse downloaded Anthropic docs into benchmarks.csv

Reads HTML/PDF sources from data/raw/ and produces a structured CSV of
all benchmark claims, tagged by source ID and confidence level.

Usage:
    python scripts/parse/extract_benchmarks.py
"""

import csv
import json
import re
from pathlib import Path

RAW_DIR = Path("data") / "raw"
PROCESSED_DIR = Path("data") / "processed"
OUTPUT_CSV = PROCESSED_DIR / "benchmarks.csv"

# ── Known benchmark records from primary sources (manually verified) ──────────
# These are coded from primary source documents (P1, P2, P3).
# New records should be appended here and tagged with appropriate source_id.

KNOWN_BENCHMARKS: list[dict] = [
    # Coding
    {
        "source_id": "P1",
        "model": "Claude Mythos",
        "benchmark": "SWE-bench Verified",
        "domain": "coding",
        "score": 93.9,
        "unit": "percent",
        "comparison_model": "Claude 3.5 Opus",
        "delta_pp": "+34",
        "confirmed_by_anthropic": True,
        "notes": "Glasswing project page headline figure",
    },
    {
        "source_id": "P1",
        "model": "Claude Mythos",
        "benchmark": "SWE-bench Pro",
        "domain": "coding",
        "score": 77.5,
        "unit": "percent",
        "comparison_model": "Claude 3.5 Opus",
        "delta_pp": "+30 (est.)",
        "confirmed_by_anthropic": True,
        "notes": "Reported range 77–78%; midpoint used",
    },
    # Math
    {
        "source_id": "P1",
        "model": "Claude Mythos",
        "benchmark": "USAMO / Olympiad Math",
        "domain": "mathematics",
        "score": None,
        "unit": "SOTA",
        "comparison_model": None,
        "delta_pp": None,
        "confirmed_by_anthropic": True,
        "notes": "Reported as SOTA; exact numeric not disclosed",
    },
    {
        "source_id": "P1",
        "model": "Claude Mythos",
        "benchmark": "GPQA Diamond",
        "domain": "reasoning",
        "score": None,
        "unit": "SOTA",
        "comparison_model": None,
        "delta_pp": None,
        "confirmed_by_anthropic": True,
        "notes": "Reported as SOTA; exact numeric not disclosed",
    },
    # Cyber
    {
        "source_id": "P1",
        "model": "Claude Mythos",
        "benchmark": "Cybench",
        "domain": "cybersecurity",
        "score": None,
        "unit": "SOTA",
        "comparison_model": None,
        "delta_pp": None,
        "confirmed_by_anthropic": True,
        "notes": "Reported as SOTA",
    },
    {
        "source_id": "P1",
        "model": "Claude Mythos",
        "benchmark": "CyberGym",
        "domain": "cybersecurity",
        "score": None,
        "unit": "SOTA",
        "comparison_model": None,
        "delta_pp": None,
        "confirmed_by_anthropic": True,
        "notes": "Reported as SOTA",
    },
    # Context
    {
        "source_id": "P1",
        "model": "Claude Mythos",
        "benchmark": "Context Window",
        "domain": "context",
        "score": 1048576,
        "unit": "tokens",
        "comparison_model": None,
        "delta_pp": None,
        "confirmed_by_anthropic": True,
        "notes": "1M token context window confirmed",
    },
    # Capability incidents
    {
        "source_id": "P3",
        "model": "Claude Mythos",
        "benchmark": "Autonomous Zero-Day Discovery",
        "domain": "cybersecurity",
        "score": None,
        "unit": "thousands (controlled eval)",
        "comparison_model": None,
        "delta_pp": None,
        "confirmed_by_anthropic": True,
        "notes": "Controlled evaluation only; not reproduced here",
    },
    {
        "source_id": "P3",
        "model": "Claude Mythos",
        "benchmark": "Sandbox Escape",
        "domain": "cybersecurity",
        "score": 1,
        "unit": "confirmed chains",
        "comparison_model": None,
        "delta_pp": None,
        "confirmed_by_anthropic": True,
        "notes": "JIT heap spray + renderer escape + kernel bypass; single confirmed chain",
    },
]

FIELDNAMES = [
    "source_id", "model", "benchmark", "domain", "score", "unit",
    "comparison_model", "delta_pp", "confirmed_by_anthropic", "notes",
]


def extract_from_html(html_path: Path, source_id: str) -> list[dict]:
    """
    Attempt to extract benchmark numbers from downloaded HTML using regex.
    Returns a list of tentative records for manual review.
    """
    records = []
    if not html_path.exists():
        return records

    text = html_path.read_text(errors="replace")
    # Pattern: look for percentage scores near benchmark names
    pattern = re.compile(
        r"(SWE-bench|GPQA|Cybench|CyberGym|USAMO|Olympiad)\s*[^.]*?(\d{1,3}\.?\d?)\s*%",
        re.IGNORECASE,
    )
    for match in pattern.finditer(text):
        records.append({
            "source_id": source_id,
            "model": "Claude Mythos",
            "benchmark": match.group(1),
            "domain": "auto-extracted",
            "score": float(match.group(2)),
            "unit": "percent",
            "comparison_model": None,
            "delta_pp": None,
            "confirmed_by_anthropic": False,
            "notes": "Auto-extracted — requires manual verification",
        })
    return records


def build_capabilities_summary(records: list[dict]) -> dict:
    """Summarise benchmarks into a capabilities_summary.json structure."""
    by_domain: dict[str, list] = {}
    for r in records:
        domain = r["domain"]
        by_domain.setdefault(domain, []).append({
            "benchmark": r["benchmark"],
            "score": r["score"],
            "unit": r["unit"],
            "confirmed": r["confirmed_by_anthropic"],
        })
    return {
        "model": "Claude Mythos",
        "summary_generated": "2026-05-07",
        "domains": by_domain,
        "constraint_matrix_ref": "docs/01_capabilities_surface.md",
    }


def main() -> None:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Start with manually verified records
    all_records = list(KNOWN_BENCHMARKS)

    # Try to auto-extract from downloaded HTML
    html_sources = [
        (RAW_DIR / "anthropic" / "glasswing_project_page.html", "P1"),
        (RAW_DIR / "anthropic" / "mythos_cybersecurity_blog.html", "P3"),
    ]
    for html_path, source_id in html_sources:
        extracted = extract_from_html(html_path, source_id)
        if extracted:
            print(f"Auto-extracted {len(extracted)} records from {html_path.name}")
            all_records.extend(extracted)

    # Write CSV
    with OUTPUT_CSV.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(all_records)
    print(f"Wrote {len(all_records)} records to {OUTPUT_CSV}")

    # Write capabilities summary
    summary = build_capabilities_summary(all_records)
    summary_path = PROCESSED_DIR / "capabilities_summary.json"
    with summary_path.open("w") as f:
        json.dump(summary, f, indent=2)
    print(f"Wrote capabilities summary to {summary_path}")


if __name__ == "__main__":
    main()
