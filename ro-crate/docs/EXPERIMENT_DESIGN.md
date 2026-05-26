# Experiment design

> Grupo 10 — IAOS 2026 (UPM)

## 1. Pregunta de investigación

Mapear cómo las **agencias de financiación** influyen en la creación de
**software científico abierto y sostenible**, sobre un corpus controlado
de 30 papers del área de *FAIR data / research software engineering*.

Sub-preguntas operacionalizadas como queries SPARQL:

1. ¿Qué *funders* aparecen con más software resultante en GitHub?
2. ¿En qué países se acumula más popularidad (stars) del software producido?
3. ¿Qué pares de papers son temáticamente similares (≥ threshold)?
4. ¿Qué topics dominan la muestra y cuántos papers superan el umbral de probabilidad?
5. ¿Qué autores cambian de organización a lo largo del tiempo?

## 2. Hipótesis informales

- Las agencias supranacionales (CE / NIH / NSF) financian la mayor parte del software de la muestra (sesgo del área, no causal).
- El software generado por papers fundados por la misma agencia tiende a clusterizar en topics similares.
- Las afiliaciones temporales muestran movilidad significativa entre dos o tres organizaciones por autor senior.

## 3. Materiales

### 3.1 Corpus

- 30 papers seleccionados manualmente (criterio: contener al menos una sección de *Acknowledgements* y al menos una mención clara de software, idealmente con repo público).
- DOIs almacenados en `data/papers_corpus.csv`.
- PDFs descargados en `data/pdfs/` (uno por DOI, nombrado por slug).

### 3.2 Fuentes externas

| Fuente | Para qué | Acceso |
|---|---|---|
| OpenAlex | metadatos de paper, autores, afiliaciones | REST `https://api.openalex.org/works/<doi>` |
| ROR | id canónica de organizaciones y funders | REST `https://api.ror.org/v2/organizations?query=<name>` |
| ORCID | id del autor (cuando OpenAlex lo trae) | embedded in OpenAlex response |
| Grobid | parseo PDF → TEI XML | docker `lfoppiano/grobid:0.8.0` |
| HuggingFace | embeddings + NER + topic modeling | descargados al primer uso |
| GitHub API (opcional) | stars, lenguaje del repo | REST `https://api.github.com/repos/<owner>/<repo>` |

### 3.3 Modelos

- **Embeddings/similitud**: `sentence-transformers/all-MiniLM-L6-v2` (rápido, calidad probada en STS; suficiente para 30 abstracts).
- **Topic modeling**: BERTopic sobre los mismos embeddings (reutilización).
- **NER en acknowledgements**: `Jean-Baptiste/roberta-large-ner-english` (CONLL2003: PER/ORG/LOC/MISC).
- **NER de software**: `oeg/SoMeSci-software-mentions` (entrenado para *software mentions*).

## 4. Variables y umbrales

| Variable | Símbolo | Valor por defecto | Justificación |
|---|---|---|---|
| Probabilidad mínima de topic | `topic_prob_threshold` | 0.30 | BERTopic con calculate_probabilities=True suele dar distribuciones planas; 0.30 deja 1-2 topics por paper sin saturar |
| Score mínimo de similitud | `similarity_threshold` | 0.70 | Por encima de 0.70 cosine sobre MiniLM se consideran "claramente sobre el mismo tema" en STS-B |
| Score NER mínimo | `ner_score_threshold` | 0.85 | Compromiso típico precision/recall, descarta entidades dudosas |

Estos thresholds se **materializan en el KG** como propiedades del nodo
n-ario correspondiente (`iaos:topicThreshold`, `iaos:similarityThreshold`),
de modo que cualquier filtrado posterior es explícito y auditable
en SPARQL (`FILTER (?score >= ?threshold)`).

## 5. Procedimiento (pipeline)

Ver `docs/WORKFLOW.md` para el diagrama de actividades.
Resumen lineal:

```
corpus.csv → 01_fetch_metadata     (OpenAlex)
           → 03_enrich_orgs_ror    (ROR)
PDFs       → 02_extract_software   (Grobid + Softcite + URL regex)
           → 06_ner_acknowledgements (PER/ORG/MISC)
abstracts  → 04_topic_modeling     (BERTopic, threshold=0.30)
           → 05_similarity         (cosine, threshold=0.70)
ALL        → 07_build_kg           (rdflib + n-ary patterns)
           → 08_prov               (PROV-O)
           → 09_validate_shacl     (pyshacl)
           → 10_make_ro_crate      (rocrate)
```

Cada paso es **idempotente** y produce un artefacto JSON o TTL en disco
que se versionará junto con el código si es razonable de tamaño
(o referenciado por URL desde Zenodo si excede 100 MB).

## 6. Métricas

### 6.1 Para el modelo NER

`eval/gold_standard.json` contiene ≥ 30 entidades anotadas a mano (objetivo:
una por paper). El script `eval/evaluate_ner.py` calcula
**precisión, recall y F1** por tipo (PER, ORG, MISC=grant) y global.

### 6.2 Para el KG

- `wc -l kg/kg.ttl` — número de triples.
- `pyshacl` debe devolver `conforms=True` (con `severity=Warning` permitido).
- Las 5 queries SPARQL deben devolver al menos 1 resultado.

## 7. Riesgos y mitigación

| Riesgo | Mitigación |
|---|---|
| Grobid falla en PDFs con escaneo | Filtrar el corpus a PDFs nativos; documentar fallos |
| El modelo de NER de software no se carga | Fallback regex (GitHub, Zenodo) ya implementado en `02_extract_software.py` |
| OpenAlex no devuelve afiliación | Marcar `Affiliation` con `startDate` aproximado al año del paper |
| ROR no resuelve una entidad | Dejar `Organization` sin `rorId`; SHACL lo marca como `sh:Warning` |
| Pocos pares similares al threshold | Bajar threshold a 0.60 y documentar el cambio en `PROV` |

## 8. Reproducibilidad

- Imagen Docker fijada a tag concreto en `docker-compose.yml`.
- `requirements.txt` con versiones mínimas; recomendado regenerar con
  `pip-compile` para fijar el lockfile.
- `PROV` graba el modelo, el threshold y el SHA-1 de cada salida.
- Release etiquetada en GitHub → sincronizada con Zenodo → DOI.

## 9. AI use declaration

Ver `AI_USE.md`.
