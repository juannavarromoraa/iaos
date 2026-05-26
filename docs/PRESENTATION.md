# Presentation outline — 10-15 min

> *Recommendation from session 13: save a few minutes to show the demo.*

## Slide map (suggested)

| # | Slide | Speaker | Time |
|---|---|---|---|
| 1 | Title + group members | A | 30 s |
| 2 | Use case & sub-questions | A | 1 min |
| 3 | Diagram **before** vs **after** feedback (side-by-side) | B | 2 min |
| 4 | Ontology in Turtle (one zoomed snippet of n-ary) | B | 1 min |
| 5 | Workflow sketch (the SVG from docs/) | C | 1 min |
| 6 | Models & justification (one table) | C | 1 min |
| 7 | Thresholds → reified in the KG | A | 30 s |
| 8 | **Live demo**: Docker compose up + run query Q5 | D | 3 min |
| 9 | NER metrics (P/R/F1 table) | C | 1 min |
| 10 | RO-Crate + PROV + Zenodo DOI | B | 1 min |
| 11 | AI use declaration | A | 30 s |
| 12 | Limitations & future work | D | 1 min |
| 13 | Thanks & questions | all | — |

## Demo script (memorize)

```bash
docker compose up -d fuseki
# upload sample KG
curl -X POST -H "Content-Type: text/turtle" \
     --data-binary @kg/kg_sample.ttl \
     "http://localhost:3030/iaos/data?graph=https://w3id.org/iaos/kg"

# run Q5 — the killer query (author affiliation history)
curl -X POST "http://localhost:3030/iaos/query" \
     -H "Content-Type: application/sparql-query" \
     --data-binary @kg/sparql/q5_author_affiliation_history.sparql
```

Esperar a que aparezcan dos filas para Alice (UPM → Oxford). Decir
en voz alta: *"esto es lo que el patrón n-ario Affiliation nos permite
capturar; un autor con varias organizaciones a lo largo del tiempo, que
era uno de los puntos de feedback del profesor."*

## Anticipación de preguntas individuales

El enunciado dice que cada miembro recibirá 1-2 preguntas
**individuales**. Practicar respuestas cortas a:

1. ¿Por qué reificar la similitud y no usar una propiedad binaria con `score`?
   → RDF es triple, no permite atributos en aristas; reificar es el patrón W3C estándar para n-arios.
2. ¿Qué pasa si OpenAlex no devuelve ROR?
   → llamamos a la API de ROR; si tampoco resuelve, dejamos sin `rorId` y la SHACL nos avisa con un Warning.
3. ¿Por qué BERTopic y no LDA?
   → BERTopic usa embeddings semánticos; LDA usa bag-of-words y sufre con corpus pequeños como el nuestro (30 abstracts).
4. ¿Cómo aseguráis reproducibilidad si las APIs externas cambian?
   → cacheamos las respuestas en `data/metadata/` y `data/raw/`; PROV graba SHA-1 y la timestamp.
5. ¿Qué hace la NER con grant IDs?
   → no se etiquetan como una entidad CONLL típica; los extraemos con regex aplicada al span de Acknowledgements (justificado en MODEL_JUSTIFICATIONS §4).
6. ¿Cuánto cuesta el modelo n-ario en triples?
   → ~3x triples por relación frente a binaria, pero solo materializamos relaciones por encima del threshold (en Similarity), así que en práctica el grafo crece ~2x, asumible.

## Material visible durante la defensa

- Pantalla: VS Code abierto con `iaos.ttl` y `kg/sparql/q5*.sparql`.
- Otra pestaña: Fuseki UI en `localhost:3030`.
- Backup: capturas de pantalla en `docs/screenshots/` por si falla la demo.
