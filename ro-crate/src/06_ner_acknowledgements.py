"""06 — NER on the Acknowledgements section.

Strategy:
  1) Use Grobid output (TEI) to grab <div type='acknowledgement'>
     (falls back to regex scanning text for "Acknowledg(e)ment[s]" header)
  2) Run a NER model and keep entities of type PER, ORG (and optional MISC
     for grant IDs we then post-process with a regex).

Input : data/pdfs/*.pdf  (re-uses Grobid)
Output: data/raw/ner.json
  [
    { "doi_slug": "...",
      "persons":      ["Kelly Cobourn", ...],
      "organizations":["US Office of Naval Research", ...],
      "grants":       ["N00014-21-1-2437", ...] }
  ]
"""
from __future__ import annotations
import json, re
from pathlib import Path
import requests
from lxml import etree

from config import (GROBID_URL, PDFS_DIR, RAW_DIR,
                    NER_MODEL, NER_SCORE_THRESHOLD)

OUT = RAW_DIR / "ner.json"
TEI_NS = {"tei": "http://www.tei-c.org/ns/1.0"}

# Grant id patterns commonly seen in acknowledgements
GRANT_PATTERNS = [
    re.compile(r"\b[A-Z]{2,4}\s?\d{3,8}-?\d*-?\d*-?\d*\b"),    # NIH/NSF style
    re.compile(r"\b\d{6,9}\b"),                                # EU grants
]


def get_acknowledgements(tei: str) -> str:
    root = etree.fromstring(tei.encode("utf-8"))
    divs = root.findall(".//tei:back//tei:div[@type='acknowledgement']", TEI_NS)
    if not divs:
        divs = root.findall(".//tei:div[@type='acknowledgement']", TEI_NS)
    return "\n".join(" ".join(d.itertext()) for d in divs).strip()


def grobid_tei(pdf: Path) -> str:
    with pdf.open("rb") as f:
        r = requests.post(
            f"{GROBID_URL}/api/processFulltextDocument",
            files={"input": f}, timeout=300)
    r.raise_for_status()
    return r.text


_ner = None
def get_ner():
    global _ner
    if _ner is None:
        from transformers import pipeline
        _ner = pipeline("ner", model=NER_MODEL,
                        aggregation_strategy="simple")
    return _ner


def extract_grants(text: str) -> list[str]:
    hits = set()
    for pat in GRANT_PATTERNS:
        for m in pat.finditer(text):
            tok = m.group(0).strip()
            # avoid obvious false positives (years, plain numbers)
            if not tok.isdigit() or len(tok) >= 7:
                hits.add(tok)
    return sorted(hits)


def main():
    pdfs = sorted(PDFS_DIR.glob("*.pdf"))
    if not pdfs:
        print("No PDFs."); return
    ner = get_ner()
    results = []
    for pdf in pdfs:
        print(f"→ {pdf.name}")
        try:
            tei = grobid_tei(pdf)
        except Exception as e:
            print(f"  grobid: {e}"); continue
        ack = get_acknowledgements(tei)
        if not ack:
            print("  (no acknowledgements found)")
            results.append({"doi_slug": pdf.stem, "persons":[], "organizations":[], "grants":[]})
            continue
        ents = ner(ack)
        persons, orgs = [], []
        for e in ents:
            if e["score"] < NER_SCORE_THRESHOLD: continue
            tag = e["entity_group"]
            if tag == "PER":
                persons.append(e["word"].strip())
            elif tag == "ORG":
                orgs.append(e["word"].strip())
        results.append({
            "doi_slug": pdf.stem,
            "persons": sorted(set(persons)),
            "organizations": sorted(set(orgs)),
            "grants": extract_grants(ack),
            "acknowledgements_text": ack,
        })
        print(f"  {len(persons)} persons, {len(orgs)} orgs, "
              f"{len(extract_grants(ack))} grant-ids")
    OUT.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n✓ → {OUT}")


if __name__ == "__main__":
    main()
