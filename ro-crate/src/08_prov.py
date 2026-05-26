"""08 — Generate PROV trace for the sample run.

Emits kg/prov.ttl, capturing the activities, entities and agents that
participated in producing the KG. This is the "Sample run (PROV)"
deliverable.
"""
from __future__ import annotations
import datetime as dt
import hashlib, json, platform, sys

from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, PROV

from config import (INST_NS, KG_DIR, RAW_DIR, METADATA_DIR, CONFIG)

INST = Namespace(INST_NS)
PRV  = Namespace("https://w3id.org/iaos/prov/")


def sha1_of(path):
    return hashlib.sha1(path.read_bytes()).hexdigest() if path.exists() else None


def main():
    g = Graph()
    g.bind("prov", PROV); g.bind("inst", INST); g.bind("prv", PRV)

    now = dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"

    # Agents (group + software agent)
    group = INST["agent/grupo10"]
    g.add((group, RDF.type, PROV.Agent))
    g.add((group, RDFS.label, Literal("Grupo 10 — IAOS 2026")))

    pipeline = INST["agent/iaos-pipeline-v1"]
    g.add((pipeline, RDF.type, PROV.SoftwareAgent))
    g.add((pipeline, RDFS.label, Literal("IAOS pipeline v1.0.0 (Python)")))
    g.add((pipeline, PROV.actedOnBehalfOf, group))

    # Activities — one per pipeline step
    steps = [
        ("fetch_metadata",      "01_fetch_metadata.py",      METADATA_DIR / "openalex.json"),
        ("extract_software",    "02_extract_software.py",    RAW_DIR / "software_mentions.json"),
        ("enrich_orgs_ror",     "03_enrich_orgs_ror.py",     RAW_DIR / "ror.json"),
        ("topic_modeling",      "04_topic_modeling.py",      RAW_DIR / "topics.json"),
        ("similarity",          "05_similarity.py",          RAW_DIR / "similarity.json"),
        ("ner_acknowledgements","06_ner_acknowledgements.py",RAW_DIR / "ner.json"),
        ("build_kg",            "07_build_kg.py",            KG_DIR  / "kg.ttl"),
    ]
    prev_out = None
    for name, script, output_path in steps:
        act = INST[f"activity/{name}"]
        g.add((act, RDF.type, PROV.Activity))
        g.add((act, RDFS.label, Literal(name)))
        g.add((act, PROV.wasAssociatedWith, pipeline))
        g.add((act, PROV.startedAtTime, Literal(now, datatype=XSD.dateTime)))

        # The Python script entity itself
        sc = INST[f"entity/{script}"]
        g.add((sc, RDF.type, PROV.Entity))
        g.add((sc, RDFS.label, Literal(script)))
        g.add((sc, PROV.atLocation, Literal(f"src/{script}")))
        g.add((act, PROV.used, sc))

        # Configuration as a Plan
        plan = INST[f"plan/{name}"]
        g.add((plan, RDF.type, PROV.Plan))
        g.add((plan, RDFS.label, Literal(f"Plan for {name}")))
        g.add((act, PROV.qualifiedAssociation, plan))

        # Output entity
        if output_path.exists():
            out = INST[f"entity/{output_path.name}"]
            g.add((out, RDF.type, PROV.Entity))
            g.add((out, RDFS.label, Literal(output_path.name)))
            g.add((out, PROV.atLocation, Literal(str(output_path.relative_to(output_path.parents[1])))))
            h = sha1_of(output_path)
            if h:
                g.add((out, PRV.sha1, Literal(h)))
            g.add((out, PROV.wasGeneratedBy, act))
            if prev_out is not None:
                g.add((out, PROV.wasDerivedFrom, prev_out))
            prev_out = out

    # Environment / configuration recorded as a Bundle-like entity
    env = INST["entity/config"]
    g.add((env, RDF.type, PROV.Entity))
    g.add((env, RDFS.label, Literal("Pipeline configuration & runtime")))
    g.add((env, PRV.python, Literal(sys.version.split()[0])))
    g.add((env, PRV.platform, Literal(platform.platform())))
    for k, v in CONFIG.items():
        g.add((env, PRV[k], Literal(str(v))))

    out = KG_DIR / "prov.ttl"
    g.serialize(out, format="turtle")
    print(f"✓ PROV → {out}")


if __name__ == "__main__":
    main()
