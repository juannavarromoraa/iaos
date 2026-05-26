"""04 — Topic modeling on abstracts (BERTopic).

Output: data/raw/topics.json  with
  {
    "topics": [{"id": 0, "label": "...", "keywords": [...]}, ...],
    "assignments": [
       {"doi": "...", "topic_id": 0, "probability": 0.84,
        "threshold": 0.30, "kept": true}
    ],
    "model": "BERTopic + all-MiniLM-L6-v2"
  }
"""
from __future__ import annotations
import json
from pathlib import Path

from config import METADATA_DIR, RAW_DIR, EMBED_MODEL, TOPIC_PROB_THRESHOLD

IN  = METADATA_DIR / "openalex.json"
OUT = RAW_DIR / "topics.json"


def load_abstracts(works):
    """Return list of (doi, abstract_text)."""
    rows = []
    for w in works:
        # OpenAlex stores abstract as inverted index → reconstruct
        inv = w.get("abstract_inverted_index") or {}
        if not inv:
            continue
        positions = sorted(((pos, term) for term, ps in inv.items() for pos in ps))
        text = " ".join(t for _, t in positions)
        doi = w.get("doi") or w.get("id")
        rows.append((doi, text))
    return rows


def main():
    from bertopic import BERTopic
    from sentence_transformers import SentenceTransformer

    works = json.loads(IN.read_text())
    rows = load_abstracts(works)
    dois, abstracts = zip(*rows)
    print(f"Embedding {len(abstracts)} abstracts with {EMBED_MODEL} …")

    embedder = SentenceTransformer(EMBED_MODEL)
    embeddings = embedder.encode(list(abstracts), show_progress_bar=True)

    # Small corpus → relax min_topic_size
    topic_model = BERTopic(
        embedding_model=embedder,
        min_topic_size=2,
        nr_topics="auto",
        calculate_probabilities=True,
        verbose=True,
    )
    topics, probs = topic_model.fit_transform(list(abstracts), embeddings)

    # Build catalogue of topics (skip the outlier topic -1)
    catalogue = []
    for tid in sorted(set(topics)):
        if tid == -1:
            continue
        words = topic_model.get_topic(tid) or []
        catalogue.append({
            "id": int(tid),
            "label": ", ".join(w for w, _ in words[:5]),
            "keywords": [w for w, _ in words],
        })

    # Assignments above threshold
    assignments = []
    import numpy as np
    for i, doi in enumerate(dois):
        row = probs[i] if probs is not None else None
        if row is None:
            tid, p = topics[i], 1.0
            assignments.append({
                "doi": doi, "topic_id": int(tid),
                "probability": float(p),
                "threshold": TOPIC_PROB_THRESHOLD,
                "kept": p >= TOPIC_PROB_THRESHOLD and tid != -1,
            })
            continue
        for tid, p in enumerate(row):
            kept = p >= TOPIC_PROB_THRESHOLD
            if kept:
                assignments.append({
                    "doi": doi,
                    "topic_id": int(tid),
                    "probability": float(p),
                    "threshold": TOPIC_PROB_THRESHOLD,
                    "kept": True,
                })

    out = {
        "topics": catalogue,
        "assignments": assignments,
        "model": f"BERTopic + {EMBED_MODEL}",
        "threshold_used": TOPIC_PROB_THRESHOLD,
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\n✓ {len(catalogue)} topics, {len(assignments)} kept assignments → {OUT}")


if __name__ == "__main__":
    main()
