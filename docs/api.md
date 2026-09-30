# Referencia de la API (v1)

La documentación interactiva está en `/docs` (OpenAPI). Base de las rutas: `/v1`.

> Estado: Fase 1. Están activos los endpoints de estado y `POST /v1/moderate`.
> Los perfiles y cuotas llegan en la Fase 2 (ver `PLAN.md`).

## Autenticación

Cada request de moderación usa una API key en el encabezado:

```
X-API-Key: aim_...
```

La key identifica al `tenant` y sus permisos. Se almacena hasheada; nunca en claro.

## `POST /v1/moderate`

Clasifica un comentario y devuelve la acción de moderación. Requiere `X-API-Key`.
En esta fase usa el motor configurado por defecto (`AIMODERATOR_DEFAULT_ENGINE`);
el `profile_id` se incorpora en la Fase 2.

Request:

```json
{
  "text": "texto del comentario",
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

Errores: `401` (API key ausente/inválida), `422` (payload inválido), `502` (fallo del motor).

### Perfiles de uso (Fase 2)

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/v1/profiles` | Lista perfiles del tenant |
| POST | `/v1/profiles` | Crea un perfil (política + motor) |
| PATCH | `/v1/profiles/{id}` | Actualiza (incrementa versión) |
| DELETE | `/v1/profiles/{id}` | Elimina |
| POST | `/v1/profiles/{id}/activate` | Activa el perfil |

### Otros

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | `/v1/usage` | Consumo y cuotas |
| GET | `/v1/health` | Liveness |
| GET | `/v1/ready` | Readiness (verifica PostgreSQL) |
| GET | `/v1/version` | Versión del servicio |
