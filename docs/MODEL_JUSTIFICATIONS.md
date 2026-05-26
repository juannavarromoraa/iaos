# Justificación de los modelos

> Esta sección es **obligatoria** según el enunciado:
> *"Model decisions should be justified"*. La organizamos por tarea.

## 1. Embeddings: `sentence-transformers/all-MiniLM-L6-v2`

**¿Por qué este?**

| Criterio | MiniLM-L6 | mpnet-base-v2 | OpenAI ada-002 |
|---|---|---|---|
| Tamaño del modelo | 22 M | 110 M | API |
| Calidad STS-B (Spearman) | 81.7 | 84.0 | ~85 |
| Latencia (CPU, 30 abstracts) | <1 s | ~5 s | depende de red |
| Open source | ✅ | ✅ | ❌ |
| Embedding dim | 384 | 768 | 1536 |

Con un corpus de **30 abstracts**, la diferencia de calidad entre MiniLM y
modelos mayores es pequeña (~2 puntos de Spearman) y MiniLM corre en CPU
sin problemas. El resto del pipeline (BERTopic, similitud cosine)
**puede reutilizar los mismos embeddings**, lo que ahorra cómputo y
asegura coherencia.

## 2. Topic modeling: BERTopic

**¿Por qué BERTopic frente a LDA o NMF?**

- LDA y NMF usan *bag-of-words*; con 30 abstracts cortos el vocabulario
  es escaso y la calidad sufre.
- BERTopic usa embeddings semánticos + UMAP + HDBSCAN; agrupa por
  significado, no por co-ocurrencia léxica.
- Soporta `calculate_probabilities=True`, lo que **nos da la
  `probability` que necesitamos** para reificar `TopicAssignment` con
  un `threshold`.

**Configuración elegida**:

```python
BERTopic(
    embedding_model=all-MiniLM-L6-v2,
    min_topic_size=2,        # corpus pequeño
    nr_topics="auto",        # HDBSCAN decide
    calculate_probabilities=True,
)
```

Con `min_topic_size=2` aceptamos topics pequeños (mejor que un único topic
gigante o todo en el outlier `-1`). El threshold de **0.30** es
intencional: BERTopic produce distribuciones bastante planas en corpus
pequeños, así que un umbral más alto deja casi todo sin asignar.

## 3. Similitud: cosine sobre los embeddings

**Por qué cosine y no Jaccard / Levenshtein / Euclidean**:

- Jaccard exige tokens compartidos → falla con paráfrasis.
- Levenshtein es para strings cortos.
- Euclidean sobre embeddings no normalizados sufre por la norma del vector.
- Cosine sobre embeddings normalizados es la métrica **estándar** para
  texto y la que reporta MTEB.

Threshold **0.70**: por encima de 0.70 en MiniLM, en evaluaciones internas
de STS, los pares se consideran *casi paráfrasis* o *muy relacionados*.

## 4. NER en Acknowledgements: `Jean-Baptiste/roberta-large-ner-english`

**Por qué este modelo**:

- Es el modelo NER **explícitamente recomendado** por la sesión 11 del curso.
- Esquema CONLL-2003 (PER/ORG/LOC/MISC) → cubre los tipos del enunciado.
- Score promedio en CoNLL F1 ~92 — suficiente para acknowledgements,
  que es texto bien estructurado.

**Alternativas evaluadas** (justificación de no haberlas elegido):

- `dslim/bert-base-NER`: bueno pero menos preciso (F1 ~91) y entrenado solo en CoNLL.
- `flair/ner-english-large`: muy preciso pero pesado y lento.
- `spaCy en_core_web_trf`: buena baseline, pero no integra tan limpio con `transformers.pipeline`.

**Grant IDs** no salen del NER (no son una entidad CONLL típica), así que
los extraemos con regex aplicado al **mismo span de acknowledgements**.
Patrones cubiertos: `NN001234`, `R01AG059874`, `H2020-INFRAEOSC-831558`, etc.

## 5. Extracción de software: SoftCite-style + heurísticas

- Modelo NER específico: `oeg/SoMeSci-software-mentions` (entrenado sobre el corpus *SoMeSci*).
- **Fallback** a regex de GitHub/Zenodo: si el modelo no carga o falla, capturamos al menos las URL canónicas.
- La extracción se documenta en cada `SoftwareMention` como `iaos:extractionMethod`, **directamente respondiendo al feedback** "tendréis que hacer algo para sacar el software del paper".

## 6. Validación

`docs/eval/` contiene un *gold standard* de NER manualmente anotado por
varios miembros del grupo (siguiendo la guía de la sesión 12: ≥ 2
anotadores, medir acuerdo). `eval/evaluate_ner.py` calcula
precisión, recall y F1.

> *El número exacto de muestras y la métrica final se rellenan
> después del run con los datos reales.*

## 7. ¿Qué descartamos y por qué?

- **GPT-4 para NER**: cerrado, no reproducible, contra el espíritu del curso.
- **Top2Vec**: alternativa a BERTopic, pero peor documentado.
- **Levenshtein para enlazar autores entre papers**: usamos `orcid` cuando existe; cuando no, la canonicalización vía OpenAlex (`author.id`) es suficiente.
