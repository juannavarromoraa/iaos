"""Generate a small synthetic KG for demo purposes.

Three papers, three authors, two organizations (with ROR), two funders,
two topics, similarity relations and a couple of software mentions.
Useful for testing the SPARQL queries and showing the ontology in action.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD, FOAF

IAOS = Namespace("https://w3id.org/iaos/ontology#")
INST = Namespace("https://w3id.org/iaos/resource/")

g = Graph()
g.bind("iaos", IAOS); g.bind("inst", INST); g.bind("foaf", FOAF)


def add(s, p, o): g.add((s, p, o))


# ---- Papers ---------------------------------------------------------------
p1 = INST["paper/p1"]; p2 = INST["paper/p2"]; p3 = INST["paper/p3"]
for u, doi, title, year, abst in [
    (p1, "10.1093/bioinformatics/btaa001", "FOOPS!: An Ontology Pitfall Scanner", 2021,
     "We present FOOPS!, a tool for detecting pitfalls in FAIR ontologies. It analyses RDF and provides a scorecard."),
    (p2, "10.1093/bioinformatics/btaa002", "SOMEF: Extracting software metadata", 2020,
     "SOMEF extracts software metadata from README files using machine learning models trained on a curated corpus."),
    (p3, "10.5281/zenodo.999", "Containers for reproducible research", 2022,
     "We discuss container-based reproducibility and present a benchmark of Docker images for scientific workflows."),
]:
    add(u, RDF.type, IAOS.Paper)
    add(u, IAOS.doi, Literal(doi, datatype=XSD.anyURI))
    add(u, IAOS.title, Literal(title))
    add(u, IAOS.year, Literal(year, datatype=XSD.gYear))
    add(u, IAOS["abstract"], Literal(abst))


# ---- Topics ---------------------------------------------------------------
t1 = INST["topic/t-0"]; t2 = INST["topic/t-1"]
add(t1, RDF.type, IAOS.Topic); add(t1, IAOS.label, Literal("FAIR data, ontology, RDF"))
for w in ["fair", "ontology", "rdf", "metadata", "pitfall"]:
    add(t1, IAOS.keywords, Literal(w))
add(t2, RDF.type, IAOS.Topic); add(t2, IAOS.label, Literal("software, reproducibility, containers"))
for w in ["software", "container", "reproducible", "docker", "workflow"]:
    add(t2, IAOS.keywords, Literal(w))


# ---- TopicAssignment (n-ary, with threshold) ------------------------------
def topic_assign(paper, topic, prob, thr=0.30):
    ta = INST[f"ta/{paper.split('/')[-1]}-{topic.split('/')[-1]}"]
    add(ta, RDF.type, IAOS.TopicAssignment)
    add(paper, IAOS.hasTopicAssignment, ta)
    add(ta, IAOS.aboutTopic, topic)
    add(ta, IAOS.probability, Literal(prob, datatype=XSD.decimal))
    add(ta, IAOS.topicThreshold, Literal(thr, datatype=XSD.decimal))
    add(ta, IAOS.topicModel, Literal("BERTopic + all-MiniLM-L6-v2"))

topic_assign(p1, t1, 0.91)
topic_assign(p2, t2, 0.74)
topic_assign(p2, t1, 0.41)
topic_assign(p3, t2, 0.88)


# ---- SimilarityRelation (n-ary, with threshold) ---------------------------
def sim(pa, pb, score, thr=0.70):
    sr = INST[f"sim/{pa.split('/')[-1]}-{pb.split('/')[-1]}"]
    add(sr, RDF.type, IAOS.SimilarityRelation)
    add(sr, IAOS.paper1, pa); add(sr, IAOS.paper2, pb)
    add(sr, IAOS.score, Literal(score, datatype=XSD.decimal))
    add(sr, IAOS.similarityThreshold, Literal(thr, datatype=XSD.decimal))
    add(sr, IAOS.similarityMethod, Literal("cosine(all-MiniLM-L6-v2)"))

sim(p1, p2, 0.78)
sim(p2, p3, 0.81)


# ---- Authors, Affiliations (n-ary, with start/end dates), Organizations ---
a1 = INST["person/alice"]; a2 = INST["person/bob"]
add(a1, RDF.type, IAOS.Person); add(a1, IAOS.name, Literal("Alice Smith"))
add(a1, IAOS.orcid, Literal("https://orcid.org/0000-0001-1111-1111", datatype=XSD.anyURI))
add(a2, RDF.type, IAOS.Person); add(a2, IAOS.name, Literal("Bob Jones"))
add(a2, IAOS.orcid, Literal("https://orcid.org/0000-0002-2222-2222", datatype=XSD.anyURI))
add(a1, IAOS.authorOf, p1); add(a1, IAOS.authorOf, p2)
add(a2, IAOS.authorOf, p3)

upm   = INST["org/upm"]
ox    = INST["org/oxford"]
add(upm, RDF.type, IAOS.Organization)
add(upm, IAOS.name, Literal("Universidad Politécnica de Madrid"))
add(upm, IAOS.rorId, Literal("https://ror.org/03n6nwv02", datatype=XSD.anyURI))
add(upm, IAOS.country, Literal("ES"))
add(upm, IAOS.orgType, Literal("education"))

add(ox, RDF.type, IAOS.Organization)
add(ox, IAOS.name, Literal("University of Oxford"))
add(ox, IAOS.rorId, Literal("https://ror.org/052gg0110", datatype=XSD.anyURI))
add(ox, IAOS.country, Literal("GB"))
add(ox, IAOS.orgType, Literal("education"))

# Alice was at UPM (2018-2020) then at Oxford (2020-now) → two Affiliations!
aff1 = INST["aff/alice-upm"]
add(aff1, RDF.type, IAOS.Affiliation)
add(a1, IAOS.hasAffiliation, aff1)
add(aff1, IAOS.atOrganization, upm)
add(aff1, IAOS.startDate, Literal("2018-01-01", datatype=XSD.date))
add(aff1, IAOS.endDate,   Literal("2020-08-31", datatype=XSD.date))
add(aff1, IAOS.role, Literal("PhD student"))

aff2 = INST["aff/alice-oxford"]
add(aff2, RDF.type, IAOS.Affiliation)
add(a1, IAOS.hasAffiliation, aff2)
add(aff2, IAOS.atOrganization, ox)
add(aff2, IAOS.startDate, Literal("2020-09-01", datatype=XSD.date))
add(aff2, IAOS.role, Literal("Postdoc"))

aff3 = INST["aff/bob-upm"]
add(aff3, RDF.type, IAOS.Affiliation)
add(a2, IAOS.hasAffiliation, aff3)
add(aff3, IAOS.atOrganization, upm)
add(aff3, IAOS.startDate, Literal("2015-09-01", datatype=XSD.date))
add(aff3, IAOS.role, Literal("Researcher"))


# ---- Project / Funder ----------------------------------------------------
ec   = INST["org/european-commission"]
add(ec, RDF.type, IAOS.Organization)
add(ec, IAOS.name, Literal("European Commission"))
add(ec, IAOS.rorId, Literal("https://ror.org/00k4n6c32", datatype=XSD.anyURI))
add(ec, IAOS.country, Literal("BE"))
add(ec, IAOS.orgType, Literal("funder"))

g1 = INST["project/h2020-fairsfair"]
add(g1, RDF.type, IAOS.Project)
add(g1, IAOS.grantID, Literal("H2020-INFRAEOSC-831558"))
add(g1, IAOS.budget,  Literal("8000000.00", datatype=XSD.decimal))
add(p1, IAOS.fundedBy, g1)
add(p2, IAOS.fundedBy, g1)
add(g1, IAOS.providedBy, ec)

g2 = INST["project/nih-r01"]
nih = INST["org/nih"]
add(nih, RDF.type, IAOS.Organization)
add(nih, IAOS.name, Literal("National Institutes of Health"))
add(nih, IAOS.rorId, Literal("https://ror.org/01cwqze88", datatype=XSD.anyURI))
add(nih, IAOS.country, Literal("US"))
add(nih, IAOS.orgType, Literal("funder"))
add(g2, RDF.type, IAOS.Project)
add(g2, IAOS.grantID, Literal("R01AG059874"))
add(g2, IAOS.budget,  Literal("450000.00", datatype=XSD.decimal))
add(p3, IAOS.fundedBy, g2)
add(g2, IAOS.providedBy, nih)


# ---- SoftwareMention (extracted via Grobid+ML) ----------------------------
sw1 = INST["software/foops"]
add(sw1, RDF.type, IAOS.SoftwareMention)
add(sw1, IAOS.name, Literal("FOOPS!"))
add(sw1, IAOS.repoURL, Literal("https://github.com/oeg-upm/fair-ontologies", datatype=XSD.anyURI))
add(sw1, IAOS.programmingLanguage, Literal("Python"))
add(sw1, IAOS.stars, Literal(72, datatype=XSD.integer))
add(sw1, IAOS.extractionMethod, Literal("Grobid + ML/NER (SoMeSci) + URL heuristics"))
add(p1, IAOS.describesSoftware, sw1)

sw2 = INST["software/somef"]
add(sw2, RDF.type, IAOS.SoftwareMention)
add(sw2, IAOS.name, Literal("SOMEF"))
add(sw2, IAOS.repoURL, Literal("https://github.com/KnowledgeCaptureAndDiscovery/somef", datatype=XSD.anyURI))
add(sw2, IAOS.programmingLanguage, Literal("Python"))
add(sw2, IAOS.stars, Literal(108, datatype=XSD.integer))
add(sw2, IAOS.extractionMethod, Literal("Grobid + ML/NER (SoMeSci) + URL heuristics"))
add(p2, IAOS.describesSoftware, sw2)


# ---- Acknowledgements (NER-extracted) -------------------------------------
ack_org = INST["org-ack/onr"]
add(ack_org, RDF.type, IAOS.Organization)
add(ack_org, IAOS.name, Literal("US Office of Naval Research"))
add(p3, IAOS.acknowledges, ack_org)

ack_per = INST["person-ack/kelly-cobourn"]
add(ack_per, RDF.type, IAOS.Person)
add(ack_per, IAOS.name, Literal("Kelly Cobourn"))
add(p3, IAOS.acknowledges, ack_per)


# Write
out = Path("kg/kg_sample.ttl")
out.parent.mkdir(parents=True, exist_ok=True)
g.serialize(out, format="turtle")
print(f"✓ Sample KG: {len(g)} triples → {out}")
