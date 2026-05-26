"""01 — Fetch paper metadata from OpenAlex.

Input : data/papers_corpus.csv (one DOI per line, column 'doi')
Output: data/metadata/openalex.json  (list of OpenAlex Work objects)

Run:    python src/01_fetch_metadata.py
"""
from __future__ import annotations
import csv, json, time, sys
from pathlib import Path
import requests

from config import OPENALEX_BASE, OPENALEX_EMAIL, METADATA_DIR, DATA

CORPUS_CSV = DATA / "papers_corpus.csv"
OUT = METADATA_DIR / "openalex.json"


def fetch_work(doi: str) -> dict | None:
    url = f"{OPENALEX_BASE}/works/https://doi.org/{doi}"
    params = {"mailto": OPENALEX_EMAIL}
    r = requests.get(url, params=params, timeout=30)
    if r.status_code == 404:
        print(f"  [!] not found: {doi}")
        return None
    r.raise_for_status()
    return r.json()


def main() -> None:
    if not CORPUS_CSV.exists():
        sys.exit(f"Missing {CORPUS_CSV}. Create it with one DOI per row "
                 "(column header 'doi').")

    works: list[dict] = []
    with CORPUS_CSV.open() as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, 1):
            doi = row["doi"].strip()
            print(f"[{i:>2}] {doi}")
            work = fetch_work(doi)
            if work:
                works.append(work)
            time.sleep(0.1)         # polite

    OUT.write_text(json.dumps(works, indent=2, ensure_ascii=False))
    print(f"\n✓ Saved {len(works)} works → {OUT}")


if __name__ == "__main__":
    main()
