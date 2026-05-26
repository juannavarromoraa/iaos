"""09 — Validate the generated KG against SHACL shapes."""
import sys
from pathlib import Path
from pyshacl import validate

KG  = Path(__file__).resolve().parent.parent / "kg" / "kg.ttl"
SHP = Path(__file__).resolve().parent.parent / "ontology" / "shapes.shacl.ttl"
ONT = Path(__file__).resolve().parent.parent / "ontology" / "iaos.ttl"


def main():
    conforms, report_graph, report_text = validate(
        data_graph=str(KG),
        shacl_graph=str(SHP),
        ont_graph=str(ONT),
        inference="rdfs",
        serialize_report_graph="turtle",
    )
    print(report_text)
    Path("kg/shacl_report.ttl").write_bytes(report_graph)
    if not conforms:
        sys.exit("✗ SHACL validation FAILED. See kg/shacl_report.ttl")
    print("✓ SHACL OK")


if __name__ == "__main__":
    main()
