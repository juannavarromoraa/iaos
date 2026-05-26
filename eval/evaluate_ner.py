"""Compute Precision / Recall / F1 of the NER step.

Compares src/06_ner_acknowledgements.py output (data/raw/ner.json) against
the manually-curated eval/gold_standard.json.

Run:   python eval/evaluate_ner.py
"""
from __future__ import annotations
import json, sys, re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parent.parent
GOLD = ROOT / "eval" / "gold_standard.json"
PRED = ROOT / "data" / "raw" / "ner.json"


def norm(s: str) -> str:
    """Loose normalization: lowercase, strip punctuation/whitespace."""
    return re.sub(r"[^\w\s-]", "", s).strip().lower()


def metrics(tp: int, fp: int, fn: int) -> dict:
    p = tp / (tp + fp) if tp + fp else 0.0
    r = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * p * r / (p + r) if p + r else 0.0
    return {"precision": round(p, 3), "recall": round(r, 3),
            "f1": round(f1, 3), "TP": tp, "FP": fp, "FN": fn}


def main():
    if not GOLD.exists():
        sys.exit(f"Missing {GOLD}")
    if not PRED.exists():
        sys.exit(f"Missing {PRED}. Run src/06_ner_acknowledgements.py first.")

    gold = {e["doi_slug"]: e["gold_entities"] for e in json.loads(GOLD.read_text())["entries"]}
    pred_raw = json.loads(PRED.read_text())
    pred = {e["doi_slug"]: {
                "PER": e.get("persons", []),
                "ORG": e.get("organizations", []),
                "GRANT": e.get("grants", [])
            } for e in pred_raw}

    overall_tp = overall_fp = overall_fn = 0
    per_type = defaultdict(lambda: [0, 0, 0])  # tp, fp, fn

    for slug, gold_ents in gold.items():
        pred_ents = pred.get(slug, {})
        if not pred_ents:
            # nothing predicted → all gold goes to FN
            for tag, items in gold_ents.items():
                per_type[tag][2] += len(items)
                overall_fn += len(items)
            continue
        for tag in ("PER", "ORG", "GRANT"):
            g = {norm(x) for x in gold_ents.get(tag, [])}
            p = {norm(x) for x in pred_ents.get(tag, [])}
            tp = len(g & p)
            fp = len(p - g)
            fn = len(g - p)
            per_type[tag][0] += tp
            per_type[tag][1] += fp
            per_type[tag][2] += fn
            overall_tp += tp; overall_fp += fp; overall_fn += fn

    print(f"\n{'tag':<8}{'P':>10}{'R':>10}{'F1':>10}{'TP':>6}{'FP':>6}{'FN':>6}")
    print("-" * 60)
    for tag, (tp, fp, fn) in per_type.items():
        m = metrics(tp, fp, fn)
        print(f"{tag:<8}{m['precision']:>10}{m['recall']:>10}"
              f"{m['f1']:>10}{m['TP']:>6}{m['FP']:>6}{m['FN']:>6}")
    g = metrics(overall_tp, overall_fp, overall_fn)
    print("-" * 60)
    print(f"{'GLOBAL':<8}{g['precision']:>10}{g['recall']:>10}"
          f"{g['f1']:>10}{g['TP']:>6}{g['FP']:>6}{g['FN']:>6}")

    # Also dump as JSON for the report
    out = {"per_type": {t: metrics(*v) for t, v in per_type.items()},
           "global": g}
    (ROOT / "eval" / "metrics.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\n✓ Wrote eval/metrics.json")


if __name__ == "__main__":
    main()
