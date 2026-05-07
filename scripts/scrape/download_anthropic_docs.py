#!/usr/bin/env python3
"""
download_anthropic_docs.py — Phase 0 Data Collection

Downloads canonical public documents about Claude Mythos from Anthropic's
public web properties. Stores files with SHA-256 integrity hashes.

ETHICS & RULES:
1. ONLY targets public, unauthenticated URLs.
2. Respects robots.txt and rate limits (2-second delay between requests).
3. Does NOT scrape or ingest any material authored by Kye Gomez.
4. Does NOT attempt to access Glasswing's authenticated API endpoints.
5. PDF downloads are stored verbatim — no text extraction performed here.
   Use ingest_web_sources.py for preprocessing.
"""

import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

RAW_DIR = Path("data") / "raw" / "anthropic"
MANIFEST_PATH = Path("data") / "processed" / "citations_index.json"

# ── Canonical Public Sources ──────────────────────────────────────────────────
# Verified by checking anthropic.com robots.txt (User-agent: * Allow: /).
# Each entry: filename, url, source_id, confirmed_by_anthropic
TARGETS: list[dict] = [
    {
        "filename": "glasswing_project_page.html",
        "url": "https://www.anthropic.com/glasswing",
        "source_id": "P1",
        "claim_type": "model_introduction",
        "confirmed_by_anthropic": True,
    },
    {
        "filename": "mythos_cybersecurity_blog.html",
        "url": "https://red.anthropic.com/2026/mythos-preview/",
        "source_id": "P3",
        "claim_type": "cybersecurity_capabilities",
        "confirmed_by_anthropic": True,
    },
    {
        "filename": "mythos_alignment_risk_update.pdf",
        "url": "https://www-cdn.anthropic.com/79c2d46d997783b9d2fb3241de43218158e5f25c.pdf",
        "source_id": "P2",
        "claim_type": "alignment_risk_update",
        "confirmed_by_anthropic": True,
    },
]

HEADERS = {
    "User-Agent": (
        "Mythos-RE-Research-Bot/1.0 "
        "(theoretical reverse engineering project; public docs only; "
        "contact: see repository README)"
    )
}


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download_file(target: dict) -> dict | None:
    """Downloads a single target and returns a manifest entry or None on failure."""
    filename = target["filename"]
    url = target["url"]
    filepath = RAW_DIR / filename

    print(f"[{target['source_id']}] Downloading {filename}...")

    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        print(f"  FAILED: {exc}")
        return None

    content = resp.content
    file_hash = sha256_of(content)

    filepath.write_bytes(content)

    manifest_entry = {
        "source_id": target["source_id"],
        "filename": filename,
        "url": url,
        "claim_type": target["claim_type"],
        "confirmed_by_anthropic": target["confirmed_by_anthropic"],
        "sha256": file_hash,
        "downloaded_at": datetime.now(timezone.utc).isoformat(),
        "size_bytes": len(content),
    }
    print(f"  OK  → {filepath} (SHA256: {file_hash[:16]}…)")
    return manifest_entry


def load_manifest() -> list[dict]:
    if MANIFEST_PATH.exists():
        with MANIFEST_PATH.open() as f:
            return json.load(f)
    return []


def save_manifest(entries: list[dict]) -> None:
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    with MANIFEST_PATH.open("w") as f:
        json.dump(entries, f, indent=2)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    existing_ids = {e["source_id"] for e in manifest}

    print("Phase 0: Data Collection")
    print(f"Target directory: {RAW_DIR.resolve()}")
    print()

    new_entries = []
    for target in TARGETS:
        if target["source_id"] in existing_ids:
            print(f"[{target['source_id']}] Already downloaded — skipping.")
            continue
        entry = download_file(target)
        if entry:
            new_entries.append(entry)
        time.sleep(2)  # Polite delay between requests

    manifest.extend(new_entries)
    save_manifest(manifest)

    print()
    print(f"Collection complete. {len(new_entries)} new files downloaded.")
    print(f"Manifest updated: {MANIFEST_PATH.resolve()}")


if __name__ == "__main__":
    main()
