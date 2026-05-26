"""Central configuration for the IAOS pipeline.

Edit values in CONFIG below to customize thresholds, models and paths.
"""
from pathlib import Path

# --- Filesystem layout -----------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
KG_DIR = ROOT / "kg"
SAMPLE_RUN = DATA / "sample_run"
PDFS_DIR = DATA / "pdfs"                 # <-- put your 30 PDFs here
METADATA_DIR = DATA / "metadata"
RAW_DIR = DATA / "raw"

for d in (KG_DIR, METADATA_DIR, RAW_DIR, PDFS_DIR, SAMPLE_RUN):
    d.mkdir(parents=True, exist_ok=True)

# --- Namespaces ------------------------------------------------------------
IAOS_NS = "https://w3id.org/iaos/ontology#"
INST_NS = "https://w3id.org/iaos/resource/"

# --- External services -----------------------------------------------------
OPENALEX_BASE = "https://api.openalex.org"
OPENALEX_EMAIL = "your-email@upm.es"     # polite pool, change me
ROR_BASE = "https://api.ror.org/v2"
GROBID_URL = "http://localhost:8070"     # docker-compose service

# --- Models (HuggingFace) --------------------------------------------------
EMBED_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
TOPIC_MODEL_BACKBONE = EMBED_MODEL        # BERTopic uses the embed model
NER_MODEL = "Jean-Baptiste/roberta-large-ner-english"
SOFTWARE_NER_MODEL = "oeg/SoMeSci-software-mentions"   # Softcite-style

# --- Thresholds (these are the ones the feedback wanted modeled!) -----------
TOPIC_PROB_THRESHOLD = 0.30      # keep TopicAssignment only if probability >=
SIMILARITY_THRESHOLD = 0.70      # keep SimilarityRelation only if score >=
NER_SCORE_THRESHOLD  = 0.85      # discard NER entities below this confidence

CONFIG = {
    "embed_model": EMBED_MODEL,
    "topic_model": "BERTopic",
    "ner_model": NER_MODEL,
    "software_ner_model": SOFTWARE_NER_MODEL,
    "topic_prob_threshold": TOPIC_PROB_THRESHOLD,
    "similarity_threshold": SIMILARITY_THRESHOLD,
    "ner_score_threshold": NER_SCORE_THRESHOLD,
    "grobid_url": GROBID_URL,
}
