"""03 — Enrich organizations against ROR.

Reads the OpenAlex dump and, for each unique institution name,
queries ROR to obtain the canonical ROR id, country and type.

Input : data/metadata/openalex.json
Output: data/raw/ror.json     (mapping: openalex_inst_id → ROR record)
"""
from __future__ import annotations
import json, time
import requests

from config import ROR_BASE, METADATA_DIR, RAW_DIR

IN  = METADATA_DIR / "openalex.json"
OUT = RAW_DIR / "ror.json"


def ror_lookup(name: str) -> dict | None:
    """First hit from `/organizations?query=<name>`. None if no result."""
    r = requests.get(f"{ROR_BASE}/organizations",
                     params={"query": name}, timeout=30)
    r.raise_for_status()
    items = r.json().get("items", [])
    return items[0] if items else None


def collect_institutions(works: list[dict]) -> dict[str, str]:
    """Return {openalex_inst_id: display_name} for all authorships."""
    insts: dict[str, str] = {}
    for w in works:
        for a in w.get("authorships", []):
            for inst in a.get("institutions", []):
                if inst.get("id"):
                    insts[inst["id"]] = inst.get("display_name", "")
    # Funders too
    for w in works:
        for g in w.get("grants", []):
            f = g.get("funder")
            if f:
                insts[f] = g.get("funder_display_name", "")
    return insts


def main() -> None:
    works = json.loads(IN.read_text())
    insts = collect_institutions(works)
    print(f"Found {len(insts)} unique organizations to resolve against ROR.")

    out: dict[str, dict] = {}
    for i, (oa_id, name) in enumerate(insts.items(), 1):
        # OpenAlex often already provides ROR — use it when available
        # Otherwise query ROR API by name
        print(f"[{i:>3}] {name}")
        # try direct ROR via OpenAlex
        direct_ror = None
        for w in works:
            for a in w.get("authorships", []):
                for inst in a.get("institutions", []):
                    if inst.get("id") == oa_id and inst.get("ror"):
                        direct_ror = inst["ror"]
                        break
        if direct_ror:
            out[oa_id] = {"id": direct_ror, "name": name, "via": "openalex"}
            continue
        # Fallback: ROR search API
        try:
            rec = ror_lookup(name)
            if rec:
                out[oa_id] = {
                    "id": rec["id"],
                    "name": rec.get("names", [{}])[0].get("value", name),
                    "country": rec.get("locations", [{}])[0]
                                  .get("geonames_details", {}).get("country_name"),
                    "types": rec.get("types", []),
                    "via": "ror-api",
                }
            else:
                out[oa_id] = {"name": name, "via": "unresolved"}
        except Exception as e:
            print(f"  [warn] {e}")
            out[oa_id] = {"name": name, "via": "error"}
        time.sleep(0.05)

    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"\n✓ Saved → {OUT}  (resolved {sum(1 for v in out.values() if v.get('id'))}/{len(out)})")


if __name__ == "__main__":
    main()
