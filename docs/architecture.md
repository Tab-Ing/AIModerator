# Arquitectura

## Visión general

```
Cliente (empresa)
   │  POST /v1/moderate  +  X-API-Key
   ▼
FastAPI ──► Auth (API key → tenant) ──► Rate limit / cuotas
   │
   ▼
Pipeline de moderación
   1. Normalización del texto
   2. Guard anti-prompt-injection (short-circuit opcional)
   3. Selección de motor según el perfil
   4. Clasificación (Jev / LLM / local / heurístico)
   5. Policy Engine (umbrales → acción)
   6. Registro + auditoría
   │
   ▼
Respuesta: { action, categories, scores, confidence, engine, injection_detected, ... }
```

## Capas

- **API (`api/`)** — routers FastAPI v1, dependencias, validación de entrada.
- **Servicios (`services/`)** — orquestación de casos de uso.
- **Moderación (`moderation/`)** — normalización, guard anti-PI, política y pipeline.
- **Motores (`engines/`)** — implementaciones detrás de `ClassificationEngine`.
- **Datos (`db/`)** — modelos SQLAlchemy, sesiones async y repositorios.
- **Núcleo (`core/`)** — seguridad, errores, logging.

## Multi-tenant

Cada empresa es un `tenant`. El acceso se realiza con `api_keys` (almacenadas
hasheadas). **Toda** consulta filtra por `tenant_id`. Los perfiles, records, auditoría y
cuotas cuelgan del tenant.

## Perfiles de uso

Un `profile` combina:

- `engine_config`: motor primario/fallback y parámetros (p. ej. usar Jev, con LLM de
  respaldo; activar o no el guard anti-PI).
- `policy_rules`: categorías, umbrales y acción asociada (`allow`, `flag`, `hide`,
  `block`, `escalate`).

Son **versionables** y puede haber uno **activo** por tenant. `POST /v1/moderate` puede
recibir un `profile_id` explícito; si no, usa el perfil activo.

## Datos (PostgreSQL)

| Tabla | Propósito |
| --- | --- |
| `tenants` | Empresas y su configuración |
| `api_keys` | Credenciales hasheadas |
| `profiles` | Perfiles de uso (política + motor) |
| `moderation_records` | Decisiones (texto hasheado/redactado) |
| `audit_logs` | Bitácora de acciones |
| `usage_counters` | Consumo por período (cuotas) |

## Flujo asíncrono

FastAPI, SQLAlchemy y los clientes HTTP (httpx) son `async` de punta a punta. Los
motores externos se invocan con timeout y se contempla fallback/consenso.
