# Referencia de la API (v1)

La documentación interactiva está en `/docs` (OpenAPI). Base de las rutas: `/v1`.

> Estado: Fase 2. Activos: estado, `POST /v1/moderate`, perfiles, uso y cuotas.

## Autenticación

Cada request usa una API key en el encabezado:

```
X-API-Key: aim_...
```

La key identifica al `tenant` y sus **scopes**. Si la lista de scopes está vacía, la key
tiene acceso total; si no, debe incluir el scope requerido (`moderate`, `profiles:read`,
`profiles:write`, `usage:read`). Se almacena hasheada; nunca en claro.

## `POST /v1/moderate`

Clasifica un comentario y devuelve la acción de moderación. Requiere `X-API-Key` y el
scope `moderate`.

- Si se envía `profile_id`, se usa ese **perfil de uso** (motor + política).
- Si no, se usa el **perfil activo** del tenant; si no hay ninguno, el motor por defecto
  (`AIMODERATOR_DEFAULT_ENGINE`).
- Aplica límite de tasa por minuto y cuota diaria (`429` si se excede).

Request:

```json
{
  "text": "texto del comentario",
  "profile_id": "uuid-opcional",
  "external_id": "id-en-la-red",
  "platform": "instagram",
  "locale": "es-AR",
  "metadata": {}
}
```

Response:

```json
{
  "record_id": "uuid",
  "action": "allow",
  "categories": ["toxicity"],
  "scores": {"toxicity": 0.12, "spam": 0.03},
  "confidence": 0.94,
  "engine": "heuristic",
  "injection_detected": false,
  "text_truncated": false,
  "reasons": [],
  "latency_ms": 3
}
```

Errores: `401` (API key ausente/inválida), `403` (scope insuficiente), `404` (perfil
inexistente), `422` (payload inválido), `429` (tasa/cuota), `502` (fallo del motor).

## Perfiles de uso

Un perfil combina `engine_config` (motor primario/fallback, guard anti-PI) y
`policy_rules` (umbrales y acciones). Son versionables y solo uno puede estar activo.

| Método | Ruta | Scope | Descripción |
| --- | --- | --- | --- |
| GET | `/v1/profiles` | `profiles:read` | Lista perfiles del tenant |
| POST | `/v1/profiles` | `profiles:write` | Crea un perfil (política + motor) |
| GET | `/v1/profiles/{id}` | `profiles:read` | Obtiene un perfil |
| PATCH | `/v1/profiles/{id}` | `profiles:write` | Actualiza (incrementa `version`) |
| DELETE | `/v1/profiles/{id}` | `profiles:write` | Elimina |
| POST | `/v1/profiles/{id}/activate` | `profiles:write` | Activa el perfil |

Ejemplo de creación:

```json
{
  "name": "estricto",
  "engine_config": {"primary": "jev", "use_pi_guard": true},
  "policy_rules": {
    "thresholds": {"toxicity": 0.5, "prompt_injection": 0.4},
    "actions": {"toxicity": "hide", "prompt_injection": "block"}
  }
}
```

## `POST /v1/moderate/batch`

Modera hasta **100** comentarios con un mismo perfil (scope `moderate`). Los resultados
respetan el orden de entrada y la cuota se descuenta por la cantidad de ítems.

```json
{"profile_id": "uuid-opcional",
 "items": [{"text": "hola"}, {"text": "sos un idiota"}]}
```

Devuelve `{"count": 2, "results": [ ... ]}`.

## Uso y cuotas

`GET /v1/usage` (scope `usage:read`) devuelve el consumo diario y la cuota:

```json
{"plan": "free", "period": "2026-09-30", "used": 12, "quota": 1000, "remaining": 988}
```

## Otros

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/v1/health` | Liveness |
| GET | `/v1/ready` | Readiness (verifica PostgreSQL) |
| GET | `/v1/version` | Versión del servicio |
| GET | `/metrics` | Métricas Prometheus (fuera de `/v1`) |
| POST | `/v1/jobs/moderate` | Encola un lote asíncrono (`202` + `job_id`) |
| GET | `/v1/jobs/{job_id}` | Estado/resultado del trabajo |

### Trabajos asíncronos (cola Redis)

`POST /v1/jobs/moderate` requiere el scope `moderate` y la cola habilitada
(`AIMODERATOR_QUEUE_ENABLED=true`). Devuelve `{"job_id": "...", "status": "queued"}`;
`GET /v1/jobs/{job_id}` responde `{"job_id", "status", "result"}` (el `result` tiene la
misma forma que `/v1/moderate/batch`).
