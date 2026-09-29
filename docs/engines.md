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

Modelo *System One* de [Jev AI](https://jevai.net): entrada no estructurada y salida
**tipada y calibrada**, sin generación de texto libre, en decenas/cientos de ms.

- Endpoint conceptual: `POST /v1/decide` con `{ "input": ..., "schema": {...} }`.
- Salida típica: `{ "route": ..., "score": 0.94, "confidence": 0.97 }`.
- Esquema de moderación previsto: `{ toxicity, harassment, hate, spam, prompt_injection, action }`.
- Ventajas: latencia baja, costo bajo, sin alucinaciones, confianza calibrada.
- Rol: **primer filtro** por defecto y detector de jailbreak/prompt-injection.
- Config: `AIMODERATOR_JEV_*` (base URL, modelo, API key). *Endpoints/autenticación
  exactos a confirmar con el proveedor.*

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
