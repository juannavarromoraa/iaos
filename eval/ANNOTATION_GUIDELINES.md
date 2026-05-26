# Annotation guidelines — NER on Acknowledgements

> Sesión 12 del curso: *"Have more than 1 annotator validating your
> responses! Measure agreement and report it."*

## 1. Procedimiento

1. **Dos anotadores** del grupo, independientes, sin comunicarse durante la anotación.
2. Cada anotador lee la sección *Acknowledgements* de los 30 PDFs y rellena su versión de `gold_standard.json` (o un Google Sheet exportado luego).
3. Se calcula el acuerdo (Cohen's kappa) con `eval/agreement.py` (a crear si quieres ir más allá; ver §5).
4. Conflictos: tercer anotador del grupo resuelve.
5. La versión final consolidada queda en `eval/gold_standard.json`.

## 2. Esquema de etiquetas

- **PER**: nombre completo de una persona física agradecida ("we thank X").
  - Sí: "Daniel Garijo", "Kelly Cobourn"
  - No: "the reviewer", "our colleagues" (sin nombre propio)
- **ORG**: organización o institución agradecida o financiadora.
  - Sí: "NIH", "European Commission", "US Office of Naval Research"
  - No: "the committee", "the project consortium" (sin nombre canónico)
- **GRANT**: identificador alfanumérico de un grant.
  - Sí: `R01AG059874`, `831558`, `H2020-INFRAEOSC-831558`, `PID2020-1234-X`
  - No: años aislados, números de página, números genéricos (`100`)

## 3. Reglas de span

- Span **mínimo y autosuficiente**: capturar el nombre canónico, sin artículos ni cargos.
  - "the European Commission" → "European Commission".
  - "Prof. Daniel Garijo" → "Daniel Garijo".
- Si la misma entidad aparece varias veces, anótese **una sola vez** en la lista (se trata como conjunto, no como secuencia).
- Acrónimos y nombre completo: anotar **ambos** si aparecen ("NIH (National Institutes of Health)" → 2 entradas).

## 4. Casos límite

| Caso | Decisión |
|---|---|
| "the authors thank anonymous reviewers" | No anotar (no es entidad nombrada) |
| "this paper is based on work supported by NSF Grant CCF-1234567" | ORG=NSF, GRANT=CCF-1234567 |
| "we acknowledge use of TACC's Stampede2 system" | ORG=TACC (sí), Stampede2 sería SOFTWARE pero NO se anota aquí (eso lo trabaja Paso 02) |
| "Drs. A. Smith and B. Jones" | 2 PER ("A. Smith", "B. Jones") |

## 5. (Opcional) Agreement

Para Cohen's kappa puedes usar `sklearn.metrics.cohen_kappa_score` sobre
los conjuntos binarios por entidad-tipo. Si te quieres ahorrar el cálculo,
basta con reportar **% de acuerdo** y conflicto resueltos.
