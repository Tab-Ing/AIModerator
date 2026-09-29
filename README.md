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
- **Doble licencia:** AGPL-3.0-or-later para uso libre; licencia comercial negociada
  para empresas.

## Estado

Fase 0 (scaffolding) completada. Ver [`PLAN.md`](PLAN.md) y [`MEMORY.md`](MEMORY.md).

## Inicio rápido

```bash
make venv        # crea .venv e instala dependencias
cp .env.example .env
make docker-up   # levanta PostgreSQL (+ API)
make migrate     # aplica migraciones
make dev         # API en http://localhost:8000/docs
```

Tests y calidad:

```bash
make lint typecheck test
```

## Documentación

- [`docs/architecture.md`](docs/architecture.md) — arquitectura general.
- [`docs/prompt-injection.md`](docs/prompt-injection.md) — defensa anti-prompt-injection.
- [`docs/engines.md`](docs/engines.md) — motores de clasificación.
- [`docs/api.md`](docs/api.md) — referencia de la API.
- [`AGENTS.md`](AGENTS.md) — lineamientos de desarrollo.

## Licencias

- Código del núcleo: [AGPL-3.0-or-later](LICENSE).
- Uso comercial/enterprise: [licencia comercial](LICENSE-COMMERCIAL.md).
- Contribuciones: requieren [CLA](CLA.md).
