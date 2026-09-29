# Referencia de la API (v1)

La documentación interactiva está en `/docs` (OpenAPI). Base de las rutas: `/v1`.

> Estado: Fase 0. Solo los endpoints de estado están activos; el resto llega en fases
> siguientes (ver `PLAN.md`).

## Autenticación

Cada request de moderación usa una API key en el encabezado:

```
X-API-Key: aim_...
```

La key identifica al `tenant` y sus permisos. Se almacena hasheada; nunca en claro.

## Endpoints previstos

### `POST /v1/moderate`

Clasifica un comentario según un perfil.

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
  "engine": "jev",
  "injection_detected": false,
  "latency_ms": 87
}
```

### Perfiles de uso

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
