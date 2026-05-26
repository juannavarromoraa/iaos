# AI use declaration

> *"AI use declaration is mandatory"* — enunciado del Entregable 2,
> sesión 9, slide 56.

Grupo 10 ha utilizado herramientas de IA durante la realización de este
trabajo. A continuación describimos **qué se usó, para qué y cómo**.

## 1. Herramientas usadas

| Herramienta | Versión / modelo | Uso |
|---|---|---|
| ChatGPT (OpenAI) | GPT-4o, GPT-5 (web) | Lluvia de ideas iniciales, redacción de borradores, depuración rápida |
| Claude (Anthropic) | Claude Opus 4.7 (web) | Análisis del feedback del profesor, refactor del diagrama y de la ontología, asistencia en la redacción del pipeline y de la documentación |
| GitHub Copilot | extension VS Code | Autocompletar en código Python (no en TTL ni Markdown) |

## 2. Modelos de **ejecución** del pipeline (no asistencia)

Estos son los modelos que **forman parte del experimento mismo** y se
documentan en `docs/MODEL_JUSTIFICATIONS.md`:

- `sentence-transformers/all-MiniLM-L6-v2` — embeddings.
- `BERTopic` — topic modeling.
- `Jean-Baptiste/roberta-large-ner-english` — NER de acknowledgements.
- `oeg/SoMeSci-software-mentions` — NER de menciones de software.

Estos sí están **integrados en el código entregable** y se ejecutan al
correr el pipeline. Los anteriores (ChatGPT, Claude, Copilot) **no** se
ejecutan en producción.

## 3. Para qué se ha usado IA generativa (uso humano)

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

## 4. Para qué NO se ha usado IA

- **NO** se ha usado IA para fabricar resultados experimentales, métricas o anotaciones del *gold standard*.
- **NO** se ha usado IA para evaluar el rendimiento del NER (se hizo a mano sobre `eval/gold_standard.json`).
- **NO** se han subido al modelo papers con copyright sin permiso explícito; solo abstracts y secciones de acknowledgements, ambos de acceso abierto.
- **NO** se han usado modelos cerrados para tareas que el enunciado pide reproducibles (NER, embeddings, topic modeling): todos los modelos del pipeline son abiertos y vienen de HuggingFace.

## 5. Política de revisión

Cada artefacto generado con asistencia de IA pasó por **al menos un
miembro del grupo distinto** del que pidió la generación, antes de
quedar en `main`. Los commits llevan firma de quien revisó.

## 6. Limitaciones conocidas

- Las herramientas conversacionales (ChatGPT/Claude) tienen *knowledge cutoff*: los detalles de OpenAlex/ROR/Grobid se verificaron contra la documentación oficial antes de implementar.
- Copilot puede sugerir código con problemas de licencia; las funciones aceptadas son utilitarias estándar (parsing JSON, formato de fechas, etc.) sin contenido protegido.

---

*Esta declaración se actualizará si durante la preparación de la defensa
se incorpora algún uso adicional de IA.*
