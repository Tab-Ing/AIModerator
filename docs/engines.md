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

Cliente compatible con la API OpenAI (`/chat/completions`), configurable por
`base_url` y `model` (DeepSeek, OpenAI, etc.). Se usa con:

- Salida en JSON validada por Pydantic.
- Comentario tratado como dato no confiable (ver `docs/prompt-injection.md`).
- Rol: análisis en profundidad, casos ambiguos, fallback.

## Local — `LocalMLEngine`

` sentence-transformers` / clasificador zero-shot, ejecutado on-premise. Requiere el
extra opcional `local` (`make install-local`). Útil cuando no se pueden enviar datos a
terceros. Rol: fallback privado o consenso.

## Heurístico — `HeuristicEngine`

Reglas y listas de bloqueo (regex/deny-list) más el detector de prompt-injection. Muy
rápido y determinista; sin costo. Rol: short-circuit barato y saneamiento previo.

## Selección y composición

El `engine_config` del perfil define el motor primario y los fallbacks. El `registry`
resuelve la implementación por nombre y el pipeline aplica fallback ante errores o
timeouts, y opcionalmente consenso entre motores.
