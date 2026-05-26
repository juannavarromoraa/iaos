"""02 — Extract software mentions from PDFs.

Pipeline:
  1) Grobid (running at GROBID_URL) parses each PDF into TEI XML
  2) For every <p> in the body we run a software-NER model
     (Softcite-style: oeg/SoMeSci-software-mentions or fallback regex)
  3) Optionally cross-check GitHub for star count / language

Input : data/pdfs/<doi-slug>.pdf      (one PDF per paper)
Output: data/raw/software_mentions.json
"""
from __future__ import annotations
import json, re, time
from pathlib import Path
import requests
from lxml import etree

from config import GROBID_URL, PDFS_DIR, RAW_DIR, SOFTWARE_NER_MODEL

TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}
OUT = RAW_DIR / "software_mentions.json"

# Lightweight URL/repo heuristic regexes — used as a fallback if NER misses
GITHUB_RE = re.compile(
    r"https?://(?:www\.)?github\.com/[\w.-]+/[\w.-]+", re.IGNORECASE)
ZENODO_RE = re.compile(r"https?://(?:doi\.org/10\.5281/)?zenodo\.org/[^\s)]+")


def grobid_extract(pdf: Path) -> str:
    """Send PDF to GROBID and return TEI XML as string."""
    with pdf.open("rb") as f:
        files = {"input": f}
        params = {"consolidateHeader": 0, "segmentSentences": 0}
        r = requests.post(
            f"{GROBID_URL}/api/processFulltextDocument",
            files=files, data=params, timeout=300,
        )
    r.raise_for_status()
    return r.text


def paragraphs(tei: str) -> list[str]:
    """Extract body paragraphs from TEI XML."""
    root = etree.fromstring(tei.encode("utf-8"))
    out: list[str] = []
    for p in root.findall(".//tei:body//tei:p", TEI_NS):
        text = " ".join(p.itertext()).strip()
        if text:
            out.append(text)
    return out


# --------------------------------------------------------------------------- #
# Software NER using HuggingFace                                              #
# --------------------------------------------------------------------------- #
_ner = None  # lazy

def get_ner():
    global _ner
    if _ner is None:
        from transformers import pipeline
        try:
            _ner = pipeline(
                "ner", model=SOFTWARE_NER_MODEL,
                aggregation_strategy="simple",
            )
        except Exception as e:                        # model not available
            print(f"  [warn] could not load {SOFTWARE_NER_MODEL}: {e}")
            print( "  → falling back to regex-only extraction")
            _ner = "regex"
    return _ner


def extract_software_from_text(text: str) -> list[dict]:
    """Return list of {name, url?, context} mentions."""
    ner = get_ner()
    mentions: list[dict] = []
    # 1) NER (if available)
    if ner != "regex":
        try:
            for ent in ner(text[:4000]):
                if ent["entity_group"].lower().startswith("soft"):
                    mentions.append({
                        "name": ent["word"],
                        "score": float(ent["score"]),
                        "context": text[max(0, ent["start"]-50): ent["end"]+50],
                    })
        except Exception as e:
            print(f"  [warn] NER failed on chunk: {e}")
    # 2) URL heuristics — always run, augment NER
    for m in GITHUB_RE.finditer(text):
        mentions.append({
            "name": m.group(0).rsplit("/", 1)[-1],
            "url": m.group(0),
            "score": 1.0,
            "context": text[max(0, m.start()-80): m.end()+80],
            "source": "regex-github",
        })
    for m in ZENODO_RE.finditer(text):
        mentions.append({
            "name": "(zenodo record)",
            "url": m.group(0),
            "score": 1.0,
            "context": text[max(0, m.start()-80): m.end()+80],
            "source": "regex-zenodo",
        })
    return mentions


def main() -> None:
    pdfs = sorted(PDFS_DIR.glob("*.pdf"))
    if not pdfs:
        print(f"No PDFs in {PDFS_DIR}. Drop your 30 PDFs there.")
        return

    all_mentions: dict[str, list] = {}
    for pdf in pdfs:
        key = pdf.stem
        print(f"→ {pdf.name}")
        try:
            tei = grobid_extract(pdf)
        except Exception as e:
            print(f"  [error] grobid failed: {e}")
            continue
        mentions: list[dict] = []
        for p in paragraphs(tei):
            mentions.extend(extract_software_from_text(p))
        # dedup by URL or name
        seen = set(); uniq = []
        for m in mentions:
            k = m.get("url") or m["name"].lower()
            if k not in seen:
                seen.add(k); uniq.append(m)
        all_mentions[key] = uniq
        print(f"   {len(uniq)} software mention(s)")

    OUT.write_text(json.dumps(all_mentions, indent=2, ensure_ascii=False))
    print(f"\n✓ Saved → {OUT}")


if __name__ == "__main__":
    main()
