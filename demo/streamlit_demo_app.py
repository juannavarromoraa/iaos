"""
IAOS — Demo Streamlit app for Entregable 2.

Consumes the IAOS Knowledge Graph either locally (kg/kg_sample.ttl) or via a
Fuseki SPARQL endpoint. Renders the five canonical case-use queries
(Q1–Q5) in interactive tabs.

Run with:
    streamlit run demo/app.py

The "Endpoint" sidebar lets you switch between:
- Local TTL (default — works without Fuseki running)
- Fuseki at http://localhost:3030/iaos/query (recommended for the demo)
"""

from pathlib import Path

import pandas as pd
import streamlit as st
from rdflib import Graph

# -------- Sidebar ------------------------------------------------------------

st.set_page_config(
    page_title="IAOS — Research Software Funding KG",
    page_icon="🧪",
    layout="wide",
)

st.sidebar.title("⚙️ Config")
mode = st.sidebar.radio(
    "KG source",
    ["Local TTL (kg/kg_sample.ttl)", "Fuseki (http://localhost:3030/iaos)"],
    help=(
        "Use Local TTL for an offline demo; switch to Fuseki for the live "
        "demo we present in class."
    ),
)
endpoint = "http://localhost:3030/iaos/query"

ROOT = Path(__file__).parent.parent
TTL_FILE = ROOT / "kg" / "kg.ttl"

# -------- Query execution helpers --------------------------------------------


@st.cache_resource
def load_local_graph() -> Graph:
    g = Graph()
    g.parse(str(TTL_FILE), format="turtle")
    return g


def run_sparql(query: str) -> pd.DataFrame:
    """Run a SPARQL SELECT and return a pandas DataFrame."""
    if mode.startswith("Local"):
        g = load_local_graph()
        results = g.query(query)
        rows = [
            {str(v): str(row[v]) if row[v] is not None else "" for v in row.labels}
            for row in results
        ]
    else:
        # Fuseki path — uses SPARQLWrapper for robustness
        from SPARQLWrapper import SPARQLWrapper, JSON

        sparql = SPARQLWrapper(endpoint)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        ans = sparql.query().convert()
        rows = [
            {k: v["value"] for k, v in binding.items()}
            for binding in ans["results"]["bindings"]
        ]
    return pd.DataFrame(rows)


# -------- Header -------------------------------------------------------------

st.title("🧪 IAOS — Research Software Funding KG")
st.markdown(
    """
**Group 10** · IA y Open Science 2026 · UPM ·
[GitHub](https://github.com/juannavarromoraa/iaos)

Demo for the 5 case-use questions (Q1–Q5). Each tab queries the KG and
renders the answer.
"""
)

# -------- Q1: Funders → software in GitHub ----------------------------------

Q1 = """
PREFIX iaos: <https://w3id.org/iaos/ontology#>
PREFIX schema: <http://schema.org/>

SELECT ?funderName (COUNT(DISTINCT ?software) AS ?nSoftware)
WHERE {
  ?paper a iaos:Paper ;
         iaos:acknowledges ?funder ;
         iaos:resultsInSoftware ?software .
  ?funder schema:name ?funderName .
  ?software iaos:codeRepository ?repo .
  FILTER(CONTAINS(LCASE(STR(?repo)), "github.com"))
}
GROUP BY ?funderName
ORDER BY DESC(?nSoftware)
"""

Q2 = """
PREFIX iaos: <https://w3id.org/iaos/ontology#>
PREFIX schema: <http://schema.org/>

SELECT ?country (COUNT(DISTINCT ?software) AS ?nSoftware) (SUM(?stars) AS ?totalStars)
WHERE {
  ?paper a iaos:Paper ;
         iaos:hasAuthor ?author ;
         iaos:resultsInSoftware ?software .
  ?author iaos:hasAffiliation ?affil .
  ?affil iaos:affiliatedTo ?org .
  ?org schema:addressCountry ?country .
  ?software iaos:stars ?stars .
}
GROUP BY ?country
ORDER BY DESC(?nSoftware)
"""

Q3 = """
PREFIX iaos: <https://w3id.org/iaos/ontology#>

SELECT ?paper ?budget ?stars
WHERE {
  ?paper a iaos:Paper ;
         iaos:fundedBy ?grant ;
         iaos:resultsInSoftware ?sw .
  ?grant iaos:budget ?budget .
  ?sw iaos:stars ?stars .
}
ORDER BY DESC(?budget)
"""

Q4 = """
PREFIX iaos: <https://w3id.org/iaos/ontology#>

SELECT ?topicLabel (COUNT(DISTINCT ?paper) AS ?nPapers)
WHERE {
  ?paper a iaos:Paper ;
         iaos:hasTopicAssignment ?ta .
  ?ta iaos:topic ?topic ;
      iaos:probability ?p ;
      iaos:threshold ?th .
  FILTER(?p >= ?th)
  ?topic iaos:topicLabel ?topicLabel .
}
GROUP BY ?topicLabel
ORDER BY DESC(?nPapers)
"""

Q5 = """
PREFIX iaos: <https://w3id.org/iaos/ontology#>
PREFIX schema: <http://schema.org/>

SELECT ?authorName ?orgName ?role ?startDate ?endDate
WHERE {
  ?author a iaos:Person ;
          schema:name ?authorName ;
          iaos:hasAffiliation ?affil .
  ?affil iaos:affiliatedTo ?org ;
         iaos:role ?role ;
         iaos:startDate ?startDate .
  ?org schema:name ?orgName .
  OPTIONAL { ?affil iaos:endDate ?endDate }
}
ORDER BY ?authorName ?startDate
"""

# -------- Tabs ---------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["Q1 Funders", "Q2 Countries", "Q3 Budget vs Quality", "Q4 Topics", "Q5 Affiliations", "🔎 SPARQL"]
)

with tab1:
    st.header("Q1 — Which funders finance the most GitHub software?")
    st.markdown(
        "*Counts distinct pieces of software per funder, filtering for "
        "those whose repository URL contains `github.com`.*"
    )
    df1 = run_sparql(Q1)
    if df1.empty:
        st.info("No results yet — run the pipeline first or load the sample KG.")
    else:
        df1["nSoftware"] = pd.to_numeric(df1["nSoftware"], errors="coerce")
        st.bar_chart(df1.set_index("funderName")["nSoftware"])
        st.dataframe(df1, use_container_width=True)

with tab2:
    st.header("Q2 — In which countries is the most popular software produced?")
    st.markdown("*Aggregates by primary author affiliation country.*")
    df2 = run_sparql(Q2)
    if df2.empty:
        st.info("No results yet.")
    else:
        df2["nSoftware"] = pd.to_numeric(df2["nSoftware"], errors="coerce")
        df2["totalStars"] = pd.to_numeric(df2["totalStars"], errors="coerce")
        col_a, col_b = st.columns(2)
        col_a.bar_chart(df2.set_index("country")["nSoftware"])
        col_b.bar_chart(df2.set_index("country")["totalStars"])
        st.dataframe(df2, use_container_width=True)

with tab3:
    st.header("Q3 — Connection between funding budget and software quality?")
    st.markdown(
        "*Scatter of grant budget (USD-equivalent) vs GitHub stars as a "
        "proxy for software adoption/quality.*"
    )
    df3 = run_sparql(Q3)
    if df3.empty:
        st.info("No results yet.")
    else:
        df3["budget"] = pd.to_numeric(df3["budget"], errors="coerce")
        df3["stars"] = pd.to_numeric(df3["stars"], errors="coerce")
        st.scatter_chart(df3, x="budget", y="stars")
        st.caption(
            "Caveat: stars are noisy and not strictly causal. We show the "
            "raw data; do not over-interpret the correlation."
        )
        st.dataframe(df3, use_container_width=True)

with tab4:
    st.header("Q4 — Papers per topic")
    st.markdown(
        "*BERTopic clusters with probability ≥ topic-specific threshold.*"
    )
    df4 = run_sparql(Q4)
    if df4.empty:
        st.info("No results yet.")
    else:
        df4["nPapers"] = pd.to_numeric(df4["nPapers"], errors="coerce")
        st.bar_chart(df4.set_index("topicLabel")["nPapers"])
        st.dataframe(df4, use_container_width=True)

with tab5:
    st.header("Q5 — Author affiliation history (n-ary pattern)")
    st.markdown(
        "*Demonstrates the reification pattern the teacher asked for: an author "
        "can belong to several organizations over their career.*"
    )
    df5 = run_sparql(Q5)
    if df5.empty:
        st.info("No results yet.")
    else:
        st.dataframe(df5, use_container_width=True)
        st.markdown(
            "**Look at Heng Li**: papers from 2009 (SAMtools) are at Wellcome "
            "Sanger; minimap2 (2018) at Broad/Dana-Farber. Same author, "
            "different `Affiliation` instance per period — exactly what the "
            "n-ary pattern was for."
        )

with tab6:
    st.header("Raw SPARQL playground")
    st.markdown(
        "Edit and run any SPARQL query against the KG. Useful for live Q&A."
    )
    default = Q5.strip()
    query = st.text_area("Query", value=default, height=200)
    if st.button("Run"):
        try:
            df = run_sparql(query)
            st.dataframe(df, use_container_width=True)
        except Exception as e:
            st.error(f"Query failed: {e}")

# -------- Footer -------------------------------------------------------------

st.sidebar.divider()
st.sidebar.caption(
    "Built for *Open Science and AI in Research Software Engineering* "
    "(UPM, 2026)."
)
