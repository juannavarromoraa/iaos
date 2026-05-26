"""10 — Package the experiment as an RO-Crate.

Uses the `rocrate` Python library (https://pypi.org/project/rocrate/).
Outputs ro-crate/ro-crate-metadata.json plus references to the
artefacts (KG, PROV, ontology, scripts, README).
"""
from pathlib import Path
from rocrate.rocrate import ROCrate

ROOT = Path(__file__).resolve().parent.parent
CRATE_DIR = ROOT / "ro-crate"


def main():
    crate = ROCrate()
    crate.name = "IAOS — Research Software Funding KG (Grupo 10)"
    crate.description = (
        "RO-Crate packaging the Knowledge Graph that links scientific "
        "papers, their authors, organizations (ROR), funding projects, "
        "topics and extracted software, plus the pipeline that produced it."
    )
    crate.creator = {
        "@id": "https://example.org/grupo10",
        "@type": "Organization",
        "name": "Grupo 10 — IAOS 2026 (UPM)",
    }
    crate.license = "https://opensource.org/licenses/MIT"

    # Add the main artefacts
    for rel in [
        "ontology/iaos.ttl",
        "ontology/shapes.shacl.ttl",
        "kg/kg.ttl",
        "kg/prov.ttl",
        "README.md",
        "docs/EXPERIMENT_DESIGN.md",
        "docs/MODEL_JUSTIFICATIONS.md",
        "docs/WORKFLOW.md",
        "AI_USE.md",
        "diagrama.drawio",
    ]:
        src = ROOT / rel
        if src.exists():
            crate.add_file(src, dest_path=rel)

    # Add the pipeline scripts as a Dataset
    src_dir = ROOT / "src"
    if src_dir.exists():
        crate.add_dataset(src_dir, dest_path="src")

    crate.write(CRATE_DIR)
    print(f"✓ RO-Crate written to {CRATE_DIR}")


if __name__ == "__main__":
    main()
