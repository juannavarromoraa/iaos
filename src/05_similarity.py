"""05 — Pairwise similarity between abstracts.

We only emit relations whose cosine similarity is >= SIMILARITY_THRESHOLD,
which is what the n-ary SimilarityRelation node reifies in the KG.

Output: data/raw/similarity.json
  [
    {"paper1": "<doi>", "paper2": "<doi>",
     "score": 0.83, "threshold": 0.70,
     "method": "cosine(all-MiniLM-L6-v2)"},
    ...
  ]
"""
from __future__ import annotations
import json
from itertools import combinations

import numpy as np
from sentence_transformers import SentenceTransformer

from config import (METADATA_DIR, RAW_DIR, EMBED_MODEL,
                    SIMILARITY_THRESHOLD)

IN  = METADATA_DIR / "openalex.json"
OUT = RAW_DIR / "similarity.json"


def reconstruct_abstract(inv: dict) -> str:
    if not inv:
        return ""
    positions = sorted(((pos, term) for term, ps in inv.items() for pos in ps))
    return " ".join(t for _, t in positions)


def main():
    works = json.loads(IN.read_text())
    pairs = []
    for w in works:
        text = reconstruct_abstract(w.get("abstract_inverted_index") or {})
        if text:
            pairs.append((w.get("doi") or w["id"], text))
    if len(pairs) < 2:
        print("Not enough abstracts to compute similarity."); return

    dois, abstracts = zip(*pairs)
    print(f"Embedding {len(abstracts)} abstracts …")
    model = SentenceTransformer(EMBED_MODEL)
    embeds = model.encode(list(abstracts), normalize_embeddings=True)

    rels: list[dict] = []
    method_label = f"cosine({EMBED_MODEL.split('/')[-1]})"
    for i, j in combinations(range(len(dois)), 2):
        score = float(np.dot(embeds[i], embeds[j]))   # cosine (normalized)
        if score >= SIMILARITY_THRESHOLD:
            rels.append({
                "paper1": dois[i],
                "paper2": dois[j],
                "score": round(score, 4),
                "threshold": SIMILARITY_THRESHOLD,
                "method": method_label,
            })

    OUT.write_text(json.dumps(rels, indent=2, ensure_ascii=False))
    print(f"✓ {len(rels)} similar pairs above {SIMILARITY_THRESHOLD} → {OUT}")


if __name__ == "__main__":
    main()
