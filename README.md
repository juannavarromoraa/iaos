# Assignment 2: Sostenibilidad y Financiación del Software de Investigación

## 1. Introducción
Este repositorio contiene el trabajo del **Grupo 10** para el segundo entregable de la asignatura. El proyecto se centra en la creación de un Grafo de Conocimiento (Knowledge Graph) para analizar cómo la financiación científica influye en la creación de software abierto y sostenible.

## 2. Caso de Uso
Nuestro objetivo es mapear la relación entre las **agencias financiadoras**, los **artículos científicos** y el **software** resultante. Queremos responder a preguntas como:
* ¿Qué agencias (ej. European Commission) financian más software alojado en GitHub?
* ¿En qué países se produce el software de investigación más popular?
* ¿Existe una conexión clara entre el presupuesto de un proyecto y la calidad/mantenimiento del código?

Para más detalles, consulta la [documentación del caso de uso](./documentation/case_use.md).

## 3. Fuentes de Datos (Enriquecimiento)
Para construir y enriquecer nuestro grafo, utilizamos dos fuentes principales:
1. **API REST - [OpenAlex](https://openalex.org/):** Fuente principal para obtener metadatos de artículos, autores y enlaces a repositorios de código (GitHub).
2. **SPARQL Endpoint - [Wikidata](https://query.wikidata.org/):** Utilizada para enriquecer la información de las agencias de financiación (país, tipo de entidad, sede).

## 4. Estructura del Repositorio
/
├──* `diagrama.png`: Contiene el diagrama de la ontología.
├──* `data/`: Contiene la selección del corpus de 30 artículos (5 ejemplos preliminares ya disponibles).
├──* `documentation/`: Documento detallados sobre el diseño y el caso de uso.

## 5. Licencia
Este proyecto está bajo la Licencia **MIT**. Consulta el archivo [LICENSE](./LICENSE) para más detalles.
