# IAOS Research Software Knowledge Graph
<img width="191" height="20" alt="image" src="https://github.com/user-attachments/assets/5aa8abe7-1c83-4453-b2b3-cd1c1b6dbbae" />


## 1. ¿Qué hay aquí?

```
iaos/
├── diagrama.drawio              # Modelo de la ontología (corregido)
├── ontology/
│   ├── iaos.ttl                 # Ontología OWL en Turtle
│   └── shapes.shacl.ttl         # Restricciones SHACL
├── src/                         # Pipeline (10 scripts numerados)
├── data/
│   ├── papers_corpus.csv        # 30 DOIs (rellenar)
│   ├── pdfs/                    # 30 PDFs (descargar)
│   ├── metadata/                # → openalex.json
│   ├── raw/                     # → topics/sim/ner/software
│   └── sample_run/              # KG sintético de demo
├── kg/
│   ├── kg.ttl                   # KG final (generado por el pipeline)
│   ├── kg_sample.ttl            # KG sintético, listo para demo
│   ├── prov.ttl                 # Traza PROV
│   └── sparql/                  # 5 queries del caso de uso
├── ro-crate/
│   └── ro-crate-metadata.json   # Empaquetado del experimento
├── docs/
│   ├── EXPERIMENT_DESIGN.md
│   ├── WORKFLOW.md
│   └── MODEL_JUSTIFICATIONS.md
├── eval/                        # gold standard + métricas NER
├── docker-compose.yml           # Grobid + pipeline + Fuseki
├── Dockerfile                   # Imagen del pipeline
├── .github/workflows/ci.yml     # CI (valida ontología, SHACL, queries)
├── CITATION.cff
├── codemeta.json
├── LICENSE                      # MIT
└── README.md                    # este archivo
```
## 2. Caso de uso

Mapear cómo la **financiación científica** influye en la creación de
**software abierto y sostenible**:

- ¿Qué agencias (ej. *European Commission*) financian más software alojado en GitHub?
- ¿En qué países se produce el software de investigación más popular?
- ¿Qué papers son similares entre sí (por contenido del abstract) por encima de un umbral?
- ¿Qué autores han pasado por varias organizaciones y siguen publicando software?

Las respuestas se obtienen ejecutando las queries SPARQL de `kg/sparql/`.

## 3. Cómo ejecutar el pipeline

### Opción A — con Docker (recomendado, reproducible)

# 1) Levantar Grobid y Fuseki
```
docker compose up -d grobid fuseki
```

# 2) Construir imagen del pipeline
```
docker compose build iaos-pipeline
```

# 3) Rellenar el corpus en data/papers_corpus.csv y descargar PDFs a data/pdfs/

# 4) Ejecutar todos los pasos
```
docker compose run --rm iaos-pipeline python src/01_fetch_metadata.py
docker compose run --rm iaos-pipeline python src/02_extract_software.py
docker compose run --rm iaos-pipeline python src/03_enrich_orgs_ror.py
docker compose run --rm iaos-pipeline python src/04_topic_modeling.py
docker compose run --rm iaos-pipeline python src/05_similarity.py
docker compose run --rm iaos-pipeline python src/06_ner_acknowledgements.py
docker compose run --rm iaos-pipeline python src/07_build_kg.py
docker compose run --rm iaos-pipeline python src/08_prov.py
docker compose run --rm iaos-pipeline python src/09_validate_shacl.py
docker compose run --rm iaos-pipeline python src/10_make_ro_crate.py
```
# 5) Subir el KG al endpoint SPARQL
```
curl -X POST -H "Content-Type: text/turtle" --data-binary @kg/kg.ttl \
     "http://localhost:3030/iaos/data?graph=https://w3id.org/iaos/kg"
```

# 6) Consultar
```
curl -X POST "http://localhost:3030/iaos/query" \
     -H "Content-Type: application/sparql-query" \
     --data-binary @kg/sparql/q1_funders_with_most_software.sparql
```

### Opción B — entorno local
```

python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```
# (Grobid se necesita en localhost:8070; usa el contenedor del compose)
```
python src/01_fetch_metadata.py
```
# … etc

## 4. Demo rápida sin tu corpus

# regenerar el KG sintético + queries
```
python data/sample_run/gen_sample_kg.py
python -c "from rdflib import Graph; \
  g=Graph().parse('kg/kg_sample.ttl'); \
  print(g.query(open('kg/sparql/q5_author_affiliation_history.sparql').read()).serialize(format='txt').decode())"
```

## 5. Decisiones de modelado

Resumen en una línea por punto del feedback recibido:

| Feedback | Cómo se aborda |
|---|---|
| Thresholds + relación n-aria | Clases `TopicAssignment`, `SimilarityRelation`, `Affiliation` con atributos `threshold` |
| ROR para organizaciones | `Organization.rorId` poblado desde OpenAlex y, si falla, vía API de ROR |
| Faltan topics | Clase `Topic` + BERTopic en `src/04_topic_modeling.py` |
| Paper sin metadatos | `iaos:doi`, `iaos:title`, `iaos:abstract`, `iaos:year`, `iaos:venue` |
| Extraer software del paper | Grobid + ML/NER (`src/02_extract_software.py`); guardado en `extractionMethod` |
| Similitud no representada | n-ario `SimilarityRelation` con `paper1`/`paper2`, `score`, `threshold`, `method` |
| Autor en varias orgs en el tiempo | n-ario `Affiliation` con `startDate`/`endDate` |

Detalles y justificaciones: ver `docs/MODEL_JUSTIFICATIONS.md`.

## 6. Reproducibilidad

- **Versionado**: tags `vX.Y.Z` + release en Zenodo (ver sección 8).
- **Determinismo**: el pipeline fija seeds en `BERTopic` y `sentence-transformers` (cuando aplica). Las APIs externas (OpenAlex/ROR) son no-deterministas — por eso cacheamos `data/metadata/openalex.json` y `data/raw/ror.json`.
- **PROV**: cada ejecución genera `kg/prov.ttl` con timestamps, hashes SHA-1 de las salidas y referencias a los scripts.
- **RO-Crate**: el experimento se empaqueta en `ro-crate/` con todos los enlaces.

## 7. Licencia

MIT (ver `LICENSE`). Recomendamos también licenciar el KG bajo CC-BY-4.0
declarándolo en `void:dataset` (pendiente).

## 8. Cómo hacer una release reproducible

git tag -a v1.0.0 -m "First release for the assignment defence"
git push origin v1.0.0
# Conectar el repo con Zenodo (https://zenodo.org/account/settings/github/)
# y activar la sincronización. Al publicar el tag aparece un DOI.

Una vez hecho:
- añadir el DOI a `CITATION.cff` y `codemeta.json`,
- subir la imagen Docker a GitHub Container Registry (`ghcr.io`) o Docker Hub,
- enlazarlo todo desde el README.

## 9. Declaración de uso de IA

El Grupo 10 ha utilizado herramientas de IA durante la realización de este trabajo.

### 9.1. Herramientas usadas

| Herramienta | Versión / modelo | Uso |
|---|---|---|
| ChatGPT (OpenAI) | GPT-4o, GPT-5 (web) | Lluvia de ideas iniciales, redacción de borradores, depuración rápida |
| Claude (Anthropic) | Claude Opus 4.7 (web) | Análisis del feedback del profesor, refactor del diagrama y de la ontología, asistencia en la redacción del pipeline y de la documentación |
| GitHub Copilot | extension VS Code | Autocompletar en código Python (no en TTL ni Markdown) |

### 9.2. Modelos de ejecución del pipeline (no asistencia)

Estos son los modelos que **forman parte del experimento mismo** y se documentan en `docs/MODEL_JUSTIFICATIONS.md`:

- `sentence-transformers/all-MiniLM-L6-v2` — embeddings.
- `BERTopic` — topic modeling.
- `Jean-Baptiste/roberta-large-ner-english` — NER de acknowledgements.
- `oeg/SoMeSci-software-mentions` — NER de menciones de software.

Estos sí están **integrados en el código entregable** y se ejecutan al correr el pipeline. Los anteriores (ChatGPT, Claude, Copilot) **no** se ejecutan en producción.

### 9.3. Para qué se ha usado IA generativa (uso humano)

| Actividad | Uso de IA | Validación humana |
|---|---|---|
| Diseño inicial del esquema | Lluvia de clases candidatas con ChatGPT/Claude | Revisada y modificada por el grupo en pizarra antes de implementar |
| Corrección del diagrama tras feedback del profesor | Claude propuso patrón n-ario y atributos de threshold | Cada cambio fue contrastado con el feedback escrito del profesor (sección 1 de `docs/MODEL_JUSTIFICATIONS.md`) |
| Redacción de la ontología en Turtle | Borrador de las clases y propiedades con Claude | Revisión sintáctica con `rdflib`; ajustes manuales de prefijos y dominios |
| Restricciones SHACL | Borrador con Claude; severidades ajustadas a mano | Validación con `pyshacl` sobre el KG sintético antes de aceptar |
| Scripts Python | Esqueleto y docstrings con Claude/Copilot | Ejecutados y verificados con datos reales / sintéticos por el grupo |
| Queries SPARQL | Primer borrador con Claude | Ejecutadas contra `kg_sample.ttl` y comparadas con resultados esperados manuales |
| README, EXPERIMENT_DESIGN, WORKFLOW, MODEL_JUSTIFICATIONS | Borrador con Claude | Editados y completados a mano por el grupo (datos del grupo, decisiones internas) |
| Presentación oral | Outline con Claude | Practicada y ajustada por cada miembro del grupo |

### 9.4. Política de revisión

Cada artefacto generado con asistencia de IA pasó por al menos un miembro del grupo distinto del que pidió la generación, antes de quedar en `main`. Cada acción de la IA fue revisada por un humano.

### 9.5. Limitaciones conocidas

- Copilot puede sugerir código con problemas de licencia, las funciones aceptadas son utilitarias estándar (parsing JSON, formato de fechas, etc.) sin contenido protegido.

*Esta declaración se actualizará si durante la preparación de la defensa se incorpora algún uso adicional de IA.*
