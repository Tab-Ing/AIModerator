# Motores de clasificación

Todos los motores implementan la misma interfaz (`aimoderator.engines.base`):

```python
class ClassificationEngine(Protocol):
    name: str

    async def classify(self, request: ClassificationRequest) -> ClassificationResult: ...
```

Con `ClassificationRequest` (texto, locale, plataforma, categorías, opciones) y
`ClassificationResult` (scores, acción, confianza, flag de inyección, salida cruda).

## Jev AI — `JevEngine`

Modelo *System One* de [Jev AI](https://jevai.net) accedido vía **Defapi**
(`https://api.defapi.org`). Entrada no estructurada y salida **tipada y calibrada**,
sin generación de texto libre, en decenas/cientos de ms.

- **Endpoint**: `POST /api/v1/decisions` con `Authorization: Bearer <Clave Defapi>`.
- **Payload**:
  ```json
  { "model": "typesafe/jev-1.13",
    "state": "<texto del comentario>",
    "questions": {
      "toxicity": {"type": "noul", "instructions": "..."},
      "severity": {"type": "score", "instructions": "...", "criteria": ["limpio", "...", "crítico"]}
    } }
  ```
- **Primitivas**: `noul` (probabilidad binaria 0..1) para las categorías
  (`toxicity`, `harassment`, `hate`, `spam`, `prompt_injection`) y `score` (escala
  ordenada) para la severidad general, de la que se toma `confidence`.
- **Respuesta**: `{ "model": ..., "answers": { "<q>": {"type": ..., "noul"|"score"|"choice", "confidence", "probabilities"} }, "usage": {...} }`.
- El comentario va como `state` (**dato no confiable**); las preguntas son un esquema
  fijo de la aplicación.
- Ventajas: latencia baja, costo bajo, sin alucinaciones, confianza calibrada.
- Config: `AIMODERATOR_JEV_ENABLED`, `AIMODERATOR_JEV_BASE_URL`,
  `AIMODERATOR_JEV_MODEL`, `AIMODERATOR_JEV_API_KEY` (key de Defapi, prefijo `dk-`).
- Verificación en vivo: `.venv/bin/python scripts/check_jev.py`.

## LLM — `LLMEngine`

Cliente compatible con la API OpenAI (`POST /v1/chat/completions`), configurable por
`base_url` y `model` (DeepSeek, OpenAI, etc.). Comportamiento:

- El comentario se envía **delimitado** (`<comentario>…</comentario>`) como dato no
  confiable; nunca se concatena al system prompt.
- Se exige salida en JSON (`response_format=json_object`) y se valida con Pydantic
  (`toxicity`, `harassment`, `hate`, `spam`, `prompt_injection`, `confidence`).
- Config: `AIMODERATOR_LLM_ENABLED`, `AIMODERATOR_LLM_BASE_URL`,
  `AIMODERATOR_LLM_MODEL`, `AIMODERATOR_LLM_API_KEY`.
- Rol: análisis en profundidad, casos ambiguos, fallback/consenso.

## Local — `LocalMLEngine`

Embeddings con `sentence-transformers` ejecutados on-premise (sin salida a terceros).
Requiere el extra opcional `local` (`make install-local`); la importación es perezosa y
si falta se lanza `EngineError`. Puntúa por **similitud coseno** contra frases prototipo
por categoría.

- Config: `AIMODERATOR_LOCAL_ENABLED`, `AIMODERATOR_LOCAL_MODEL`.
- Rol: fallback privado o consenso.

## Heurístico — `HeuristicEngine`

Reglas y listas de bloqueo (regex/deny-list) más el detector de prompt-injection. Muy
rápido y determinista; sin costo. Rol: short-circuit barato y saneamiento previo.

## Selección y composición

El `engine_config` del perfil define el motor primario, los fallbacks y el modo:

```json
{
  "primary": "jev",
  "fallbacks": ["heuristic"],
  "consensus": false,
  "use_pi_guard": true
}
```

- **Fallback** (`consensus: false`): si el motor primario lanza `EngineError` (error de
  red, timeout, respuesta inválida), se intentan los fallbacks en orden.
- **Consenso** (`consensus: true`): se ejecutan primario y fallbacks en paralelo y se
  combinan los scores tomando el **máximo** por categoría; el motor reportado es
  `consensus:<a>+<b>`.

El `registry` resuelve cada motor por nombre; los motores no disponibles se omiten.
