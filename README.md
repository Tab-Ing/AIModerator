# AIModerator

API multi-tenant para **moderar comentarios de redes sociales**. Cada empresa define
uno o varios **perfiles de uso** —política de bloqueo + motor/modelo de análisis— y
obtiene una decisión de moderación por comentario vía REST.

- **Multi-tenant:** aislamiento por empresa, API keys propias y cuotas.
- **Perfiles de uso:** política de bloqueo y modelo configurables, versionables y activables.
- **Motores intercambiables:** interfaz común (`JevEngine`, `LLMEngine`, `LocalMLEngine`,
  `HeuristicEngine`).
- **Anti-prompt-injection:** el comentario es siempre dato no confiable, con
  normalización, detector dedicado y validación estricta de salidas.
- **Source-available:** gratis para uso **personal y sin fines de lucro** (ONG,
  educación, investigación) bajo PolyForm Noncommercial 1.0.0; **todo uso comercial o
  SaaS** requiere una licencia comercial negociada.
- **Panel de administración:** FastAPI + Jinja2 + HTMX en `/admin` (tenants, API keys,
  perfiles, registros, métricas).
- **Cola de trabajos:** lotes asíncronos con Redis + arq (`/v1/jobs/moderate`).

## Estado

Fases 0–4 completadas, más panel de administración y cola Redis.
Ver [`PLAN.md`](PLAN.md) y [`MEMORY.md`](MEMORY.md).

## Inicio rápido

```bash
make venv        # crea .venv e instala dependencias
cp .env.example .env
make docker-up   # levanta PostgreSQL + Redis + API (+ worker)
make migrate     # aplica migraciones
make dev         # API en http://localhost:8000/docs
make worker      # worker de arq para lotes asíncronos
```

Panel de administración: <http://localhost:8000/admin> (credenciales por
`AIMODERATOR_ADMIN_USERNAME` / `AIMODERATOR_ADMIN_PASSWORD`).

Tests y calidad:

```bash
make lint typecheck test          # unitarios
make test-integration             # requiere PostgreSQL
make test-live                    # llama a proveedores externos (requiere API key)
```

## Documentación

- [`docs/architecture.md`](docs/architecture.md) — arquitectura general.
- [`docs/prompt-injection.md`](docs/prompt-injection.md) — defensa anti-prompt-injection.
- [`docs/engines.md`](docs/engines.md) — motores de clasificación.
- [`docs/api.md`](docs/api.md) — referencia de la API.
- [`AGENTS.md`](AGENTS.md) — lineamientos de desarrollo.

## Licencias

- Uso gratuito (personal y sin fines de lucro): [PolyForm Noncommercial 1.0.0](LICENSE).
- Uso comercial o SaaS: [licencia comercial](LICENSE-COMMERCIAL.md) (se negocia).
- Contribuciones: requieren [CLA](CLA.md).

> AIModerator **no es** código abierto (Open Source). Es *source-available*: el código se
> puede ver y usar gratis solo para fines no comerciales.
