"""07 — Build the RDF Knowledge Graph.

Combines all artifacts produced by steps 01-06 and emits two files:
  - kg/kg.ttl              the actual KG
  - kg/kg.nq               n-quads (handy for triplestores like Fuseki)

CRITICAL — this is where the n-ary patterns from the diagram are written:
  * Affiliation       (Person — startDate, endDate — Organization)
  * TopicAssignment   (Paper — probability, threshold — Topic)
  * SimilarityRelation (Paper1 — score, threshold — Paper2)
"""
from __future__ import annotations
import json, hashlib, re, datetime as dt
from pathlib import Path

from rdflib import Graph, Namespace, Literal, URIRef, BNode
from rdflib.namespace import RDF, RDFS, XSD, DCTERMS, FOAF

from config import (IAOS_NS, INST_NS, METADATA_DIR, RAW_DIR, KG_DIR,
                    EMBED_MODEL, TOPIC_PROB_THRESHOLD,
                    SIMILARITY_THRESHOLD)

IAOS = Namespace(IAOS_NS)
INST = Namespace(INST_NS)


def slug(s: str) -> str:
    """Stable slug for URIs."""
    h = hashlib.sha1(s.encode("utf-8")).hexdigest()[:10]
    return re.sub(r"[^a-zA-Z0-9_-]+", "-", s.strip().lower())[:40] + "-" + h


def uri(kind: str, key: str) -> URIRef:
    return URIRef(f"{INST_NS}{kind}/{slug(key)}")


def reconstruct_abstract(inv: dict) -> str:
    if not inv: return ""
    positions = sorted(((p, t) for t, ps in inv.items() for p in ps))
    return " ".join(t for _, t in positions)


# --------------------------------------------------------------------------- #
def build_graph() -> Graph:
    g = Graph()
    g.bind("iaos", IAOS)
    g.bind("inst", INST)
    g.bind("dcterms", DCTERMS)
    g.bind("foaf", FOAF)

    # ----- Load artifacts ---------------------------------------------------
    works    = json.loads((METADATA_DIR / "openalex.json").read_text())
    ror_map  = json.loads((RAW_DIR / "ror.json").read_text())          if (RAW_DIR/"ror.json").exists()         else {}
    topics_d = json.loads((RAW_DIR / "topics.json").read_text())       if (RAW_DIR/"topics.json").exists()      else {"topics":[],"assignments":[]}
    sim      = json.loads((RAW_DIR / "similarity.json").read_text())   if (RAW_DIR/"similarity.json").exists()  else []
    soft     = json.loads((RAW_DIR / "software_mentions.json").read_text())  if (RAW_DIR/"software_mentions.json").exists() else {}
    ner      = json.loads((RAW_DIR / "ner.json").read_text())          if (RAW_DIR/"ner.json").exists()         else []
    ner_idx  = {e["doi_slug"]: e for e in ner}

    # ----- Topics -----------------------------------------------------------
    topic_uri = {}
    for t in topics_d.get("topics", []):
        u = uri("topic", f"topic-{t['id']}")
        topic_uri[t["id"]] = u
        g.add((u, RDF.type, IAOS.Topic))
        g.add((u, IAOS.label, Literal(t["label"])))
        for k in t["keywords"]:
            g.add((u, IAOS.keywords, Literal(k)))

    # ----- Papers, Authors, Affiliations, Organizations --------------------
    paper_uri = {}
    person_uri_by_oa = {}
    org_uri_by_oa   = {}

    for w in works:
        doi = w.get("doi") or w["id"]
        p_u = uri("paper", doi)
        paper_uri[doi] = p_u
        g.add((p_u, RDF.type, IAOS.Paper))
        g.add((p_u, IAOS.doi,   Literal(doi, datatype=XSD.anyURI)))
        g.add((p_u, IAOS.title, Literal(w.get("title", ""))))
        abst = reconstruct_abstract(w.get("abstract_inverted_index") or {})
        if abst:
            g.add((p_u, IAOS["abstract"], Literal(abst)))
        if w.get("publication_year"):
            g.add((p_u, IAOS.year, Literal(w["publication_year"], datatype=XSD.gYear)))
        if w.get("primary_location",{}).get("source",{}).get("display_name"):
            g.add((p_u, IAOS.venue,
                   Literal(w["primary_location"]["source"]["display_name"])))

        # ----- Authors + Affiliations (n-ary!) -------------------------------
        for a in w.get("authorships", []):
            author = a.get("author") or {}
            oa_id = author.get("id")
            if not oa_id: continue
            if oa_id not in person_uri_by_oa:
                pe_u = uri("person", oa_id)
                person_uri_by_oa[oa_id] = pe_u
                g.add((pe_u, RDF.type, IAOS.Person))
                if author.get("display_name"):
                    g.add((pe_u, IAOS.name, Literal(author["display_name"])))
                if author.get("orcid"):
                    g.add((pe_u, IAOS.orcid, Literal(author["orcid"], datatype=XSD.anyURI)))
            pe_u = person_uri_by_oa[oa_id]
            g.add((pe_u, IAOS.authorOf, p_u))

            # For each institution affiliated in THIS paper, create an
            # Affiliation n-ary node (start/end date approximated by paper year)
            for inst in a.get("institutions", []):
                oa_org = inst.get("id")
                if not oa_org: continue
                if oa_org not in org_uri_by_oa:
                    org_u = uri("organization", oa_org)
                    org_uri_by_oa[oa_org] = org_u
                    g.add((org_u, RDF.type, IAOS.Organization))
                    g.add((org_u, IAOS.name, Literal(inst.get("display_name", ""))))
                    if inst.get("country_code"):
                        g.add((org_u, IAOS.country, Literal(inst["country_code"])))
                    # ROR id (always present in OpenAlex when known)
                    ror_id = inst.get("ror") or (ror_map.get(oa_org, {}).get("id"))
                    if ror_id:
                        g.add((org_u, IAOS.rorId, Literal(ror_id, datatype=XSD.anyURI)))
                    if inst.get("type"):
                        g.add((org_u, IAOS.orgType, Literal(inst["type"])))
                org_u = org_uri_by_oa[oa_org]

                # ----- n-ary Affiliation -------------------------------------
                aff_key = f"{oa_id}__{oa_org}__{w.get('publication_year')}"
                aff_u = uri("affiliation", aff_key)
                g.add((aff_u, RDF.type, IAOS.Affiliation))
                g.add((pe_u, IAOS.hasAffiliation, aff_u))
                g.add((aff_u, IAOS.atOrganization, org_u))
                # we approximate the time window with the publication year
                y = w.get("publication_year")
                if y:
                    g.add((aff_u, IAOS.startDate,
                           Literal(f"{y}-01-01", datatype=XSD.date)))

        # ----- Grant / Funder ------------------------------------------------
        for gr in w.get("grants", []):
            award_id = gr.get("award_id") or "unknown"
            grant_u = uri("project", f"{w.get('id','?')}__{award_id}")
            g.add((grant_u, RDF.type, IAOS.Project))
            g.add((grant_u, IAOS.grantID, Literal(award_id)))
            g.add((p_u, IAOS.fundedBy, grant_u))
            funder_oa = gr.get("funder")
            if funder_oa:
                if funder_oa not in org_uri_by_oa:
                    fu = uri("organization", funder_oa)
                    org_uri_by_oa[funder_oa] = fu
                    g.add((fu, RDF.type, IAOS.Organization))
                    g.add((fu, IAOS.name, Literal(gr.get("funder_display_name",""))))
                    ror_id = ror_map.get(funder_oa, {}).get("id")
                    if ror_id:
                        g.add((fu, IAOS.rorId, Literal(ror_id, datatype=XSD.anyURI)))
                g.add((grant_u, IAOS.providedBy, org_uri_by_oa[funder_oa]))

    # ----- TopicAssignment n-ary (with threshold) --------------------------
    model_label = topics_d.get("model", "BERTopic")
    for a in topics_d.get("assignments", []):
        if not a.get("kept"): continue
        if a["doi"] not in paper_uri:        # stray doi
            continue
        ta = uri("topicassignment", f"{a['doi']}__t{a['topic_id']}")
        g.add((ta, RDF.type, IAOS.TopicAssignment))
        g.add((paper_uri[a["doi"]], IAOS.hasTopicAssignment, ta))
        g.add((ta, IAOS.aboutTopic, topic_uri[a["topic_id"]]))
        g.add((ta, IAOS.probability, Literal(a["probability"], datatype=XSD.decimal)))
        g.add((ta, IAOS.topicThreshold,
               Literal(a["threshold"], datatype=XSD.decimal)))
        g.add((ta, IAOS.topicModel, Literal(model_label)))

    # ----- SimilarityRelation n-ary ---------------------------------------
    for s in sim:
        p1 = paper_uri.get(s["paper1"]); p2 = paper_uri.get(s["paper2"])
        if not (p1 and p2): continue
        sr = uri("similarity", f"{s['paper1']}__{s['paper2']}")
        g.add((sr, RDF.type, IAOS.SimilarityRelation))
        g.add((sr, IAOS.paper1, p1))
        g.add((sr, IAOS.paper2, p2))
        g.add((sr, IAOS.score, Literal(s["score"], datatype=XSD.decimal)))
        g.add((sr, IAOS.similarityThreshold,
               Literal(s["threshold"], datatype=XSD.decimal)))
        g.add((sr, IAOS.similarityMethod, Literal(s["method"])))

    # ----- SoftwareMention (extraction Grobid+ML) --------------------------
    # software_mentions.json key is the PDF stem (doi-slug);
    # cross-reference with paper_uri via a slugified-doi map
    slug_to_uri = {slug(d): u for d, u in paper_uri.items()}
    for pdf_stem, mentions in soft.items():
        paper_match = slug_to_uri.get(pdf_stem) or paper_uri.get(pdf_stem)
        for m in mentions:
            sw = uri("software", (m.get("url") or m["name"]))
            g.add((sw, RDF.type, IAOS.SoftwareMention))
            g.add((sw, IAOS.name, Literal(m["name"])))
            if m.get("url"):
                g.add((sw, IAOS.repoURL, Literal(m["url"], datatype=XSD.anyURI)))
            g.add((sw, IAOS.extractionMethod,
                   Literal("Grobid + ML/NER (SoMeSci/Softcite + URL heuristics)")))
            if paper_match:
                g.add((paper_match, IAOS.describesSoftware, sw))

    # ----- Acknowledgements (NER → :acknowledges) --------------------------
    for entry in ner:
        paper_match = slug_to_uri.get(entry["doi_slug"])
        if not paper_match: continue
        for org_name in entry.get("organizations", []):
            o = uri("organization-ack", org_name)
            g.add((o, RDF.type, IAOS.Organization))
            g.add((o, IAOS.name, Literal(org_name)))
            g.add((paper_match, IAOS.acknowledges, o))
        for person_name in entry.get("persons", []):
            pe = uri("person-ack", person_name)
            g.add((pe, RDF.type, IAOS.Person))
            g.add((pe, IAOS.name, Literal(person_name)))
            g.add((paper_match, IAOS.acknowledges, pe))

    return g


def main():
    g = build_graph()
    out_ttl = KG_DIR / "kg.ttl"
    out_nq  = KG_DIR / "kg.nq"
    g.serialize(out_ttl, format="turtle")
    g.serialize(out_nq,  format="nquads")
    print(f"✓ {len(g):,} triples → {out_ttl}")
    print(f"  also as N-Quads → {out_nq}")


if __name__ == "__main__":
    main()
