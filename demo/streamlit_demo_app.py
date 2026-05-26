"""
IAOS — Demo Streamlit app para Entregable 2.
Usa el Knowledge Graph real con detección automática de ruta.
Queries adaptadas a la topología real del KG extraído (Autores, Organizaciones, Temáticas).
"""

from pathlib import Path
import pandas as pd
import streamlit as st
from rdflib import Graph

st.set_page_config(page_title="IAOS — Research KG Dashboard", page_icon="🧪", layout="wide")

# ── Sistema Inteligente de Rutas ──────────────────────────────────────────
posibles_rutas = [
    Path(__file__).resolve().parent / "kg" / "kg.ttl",          
    Path(__file__).resolve().parent.parent / "kg" / "kg.ttl",   
    Path("kg/kg.ttl").resolve()                                 
]

TTL_FILE = next((ruta for ruta in posibles_rutas if ruta.exists()), None)

# ── Sidebar ────────────────────────────────────────────────────────────────
st.sidebar.title("⚙️ Config")
mode = st.sidebar.radio("KG source", ["Local TTL (kg/kg.ttl)", "Fuseki (http://localhost:3030/iaos)"])
endpoint = "http://localhost:3030/iaos/query"

@st.cache_resource
def load_local_graph() -> Graph:
    g = Graph()
    if TTL_FILE: g.parse(str(TTL_FILE), format="turtle")
    return g

if mode.startswith("Local"):
    if TTL_FILE:
        g_test = load_local_graph()
        st.sidebar.success(f"🟢 Archivo encontrado:\n`{TTL_FILE.name}`")
        st.sidebar.metric("Triples RDF cargados", len(g_test))
    else:
        st.sidebar.error("🔴 No se encuentra el archivo `kg.ttl`.")

def run_sparql(query: str) -> pd.DataFrame:
    if mode.startswith("Local"):
        g = load_local_graph()
        if len(g) == 0: return pd.DataFrame()
        results = g.query(query)
        rows = [{str(var): str(row[var]) if row[var] is not None else "" for var in results.vars} for row in results]
    else:
        from SPARQLWrapper import SPARQLWrapper, JSON
        try:
            sparql = SPARQLWrapper(endpoint)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            ans = sparql.query().convert()
            rows = [{k: v["value"] for k, v in binding.items()} for binding in ans["results"]["bindings"]]
        except: return pd.DataFrame()
    return pd.DataFrame(rows)

# ── QUERIES REDISEÑADAS A LA TOPOLOGÍA REAL DEL GRAFO ──────────────────────

# Q1: Organizaciones con mayor volumen de investigadores
Q1 = """
PREFIX iaos: <https://w3id.org/iaos/ontology#>
SELECT ?orgName (COUNT(DISTINCT ?author) AS ?nAuthors)
WHERE {
  ?author a iaos:Person ;
          iaos:hasAffiliation ?affil .
  ?affil iaos:atOrganization ?org .
  ?org iaos:name ?orgName .
}
GROUP BY ?orgName
ORDER BY DESC(?nAuthors)
LIMIT 15
"""

# Q2: Producción Científica e Impacto por País
Q2 = """
PREFIX iaos: <https://w3id.org/iaos/ontology#>
SELECT ?country (COUNT(DISTINCT ?paper) AS ?nPapers) (COUNT(DISTINCT ?org) AS ?nOrgs)
WHERE {
  ?paper a iaos:Paper .
  ?author iaos:authorOf ?paper ;
          iaos:hasAffiliation ?affil .
  ?affil iaos:atOrganization ?org .
  ?org iaos:country ?country .
}
GROUP BY ?country
ORDER BY DESC(?nPapers)
"""

# Q3: Nivel de Colaboración (Papers por Autor)
Q3 = """
PREFIX iaos: <https://w3id.org/iaos/ontology#>
SELECT ?authorName (COUNT(DISTINCT ?paper) AS ?nPapers)
WHERE {
  ?author a iaos:Person ;
          iaos:name ?authorName ;
          iaos:authorOf ?paper .
}
GROUP BY ?authorName
ORDER BY DESC(?nPapers)
LIMIT 50
"""

# Q4: Clústeres Temáticos (Topic Modeling real con Threshold)
Q4 = """
PREFIX iaos: <https://w3id.org/iaos/ontology#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?topicName (COUNT(DISTINCT ?paper) AS ?nPapers)
WHERE {
  ?paper a iaos:Paper ;
         iaos:hasTopicAssignment ?ta .
  ?ta iaos:aboutTopic ?topic ;
      iaos:probability ?p ;
      iaos:topicThreshold ?th .
  FILTER(xsd:float(?p) >= xsd:float(?th))
  BIND(REPLACE(STR(?topic), "^.*[/#]", "") AS ?topicName)
}
GROUP BY ?topicName
ORDER BY DESC(?nPapers)
"""

# Q5: Red N-aria de Afiliaciones y Fechas
Q5 = """
PREFIX iaos: <https://w3id.org/iaos/ontology#>
SELECT ?authorName ?orgName ?startDate
WHERE {
  ?author a iaos:Person ;
          iaos:name ?authorName ;
          iaos:hasAffiliation ?affil .
  ?affil iaos:atOrganization ?org ;
         iaos:startDate ?startDate .
  ?org iaos:name ?orgName .
}
ORDER BY ?authorName ?startDate
LIMIT 100
"""

# ── INTERFAZ DE USUARIO ───────────────────────────────────────────────────
st.title("🧪 IAOS — Research KG Dashboard")
st.markdown("**Grupo 10** · IA y Open Science 2026 · UPM · [GitHub](https://github.com/juannavarromoraa/iaos)")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "Q1 Talento Institucional", "Q2 Impacto Global", "Q3 Top Investigadores",
    "Q4 Temáticas", "Q5 Trazabilidad N-aria", "🔎 SPARQL libre"
])

with tab1:
    st.header("Q1 — ¿Qué instituciones atraen a más investigadores?")
    df = run_sparql(Q1)
    if not df.empty:
        df["nAuthors"] = pd.to_numeric(df["nAuthors"])
        st.bar_chart(df.set_index("orgName")["nAuthors"], color="#ffaa00")
        st.dataframe(df, use_container_width=True)

with tab2:
    st.header("Q2 — Producción científica por país de afiliación")
    df = run_sparql(Q2)
    if not df.empty:
        df["nPapers"] = pd.to_numeric(df["nPapers"])
        df["nOrgs"] = pd.to_numeric(df["nOrgs"])
        col1, col2 = st.columns(2)
        col1.bar_chart(df.set_index("country")["nPapers"])
        col2.bar_chart(df.set_index("country")["nOrgs"])
        st.dataframe(df, use_container_width=True)

with tab3:
    st.header("Q3 — Investigadores con mayor producción")
    df = run_sparql(Q3)
    if not df.empty:
        df["nPapers"] = pd.to_numeric(df["nPapers"])
        st.scatter_chart(df, x="authorName", y="nPapers", color="#00ff00")
        st.dataframe(df, use_container_width=True)

with tab4:
    st.header("Q4 — Artículos por clúster temático (BERTopic)")
    df = run_sparql(Q4)
    if not df.empty:
        df["nPapers"] = pd.to_numeric(df["nPapers"])
        st.bar_chart(df.set_index("topicName")["nPapers"])
        st.dataframe(df, use_container_width=True)

with tab5:
    st.header("Q5 — Historial N-ario de Afiliaciones")
    st.markdown("Diseño que modela la cardinalidad múltiple: un autor ligado a varias instituciones a lo largo del tiempo.")
    df = run_sparql(Q5)
    if not df.empty:
        st.dataframe(df, use_container_width=True)

with tab6:
    st.header("🔎 Consola SPARQL")
    query = st.text_area("Ejecuta tus propias consultas sobre el grafo de 30 papers:", value=Q5.strip(), height=220)
    if st.button("Ejecutar"):
        st.dataframe(run_sparql(query), use_container_width=True)