# Contribuir a AIModerator

¡Gracias por tu interés! Antes de enviar cambios, leé este documento.

## Requisitos previos

- Python 3.12 o superior.
- `git`.
- PostgreSQL 16 (local o vía `docker compose`).
- Opcional: [`uv`](https://github.com/astral-sh/uv) para mayor velocidad.

## Entorno de desarrollo

**Todo el desarrollo se realiza dentro del entorno virtual `.venv`.**

```bash
make venv        # crea .venv e instala dependencias (dev)
make docker-up   # levanta PostgreSQL
cp .env.example .env
make migrate     # aplica migraciones
make dev         # levanta la API en http://localhost:8000
```

Comandos útiles:

```bash
make test              # tests unitarios (sin Postgres)
make test-integration  # tests de integración (requiere Postgres)
make lint              # ruff check
make format            # ruff format + fixes
make typecheck         # mypy
```

## Flujo de contribución

1. Hacé un fork y creá una rama: `feat/...`, `fix/...`, `docs/...`.
2. Escribí tests que cubran tu cambio.
3. Asegurate de que pasen: `make lint typecheck test`.
4. Actualizá `MEMORY.md` con un resumen del cambio.
5. Abrí un pull request describiendo el qué y el porqué.

## Convención de commits

Usamos [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(moderation): agrega motor Jev
fix(api): corrige validación de perfil
docs(prompt-injection): amplía el modelo de amenazas
```

## Licencia de las contribuciones (CLA)

Este proyecto usa **doble licencia AGPL-3.0-or-later + comercial**. Para poder ofrecer
la licencia comercial, todo aporte requiere aceptar el [`CLA.md`](CLA.md). El bot de CLA
te lo pedirá al abrir el pull request. Sin la firma, el PR no puede fusionarse.

Esto **no** cambia el requisito de que las empresas que quieran usar el software fuera
de los términos de la AGPL deban **negociar y pagar** una licencia comercial (ver
[`LICENSE-COMMERCIAL.md`](LICENSE-COMMERCIAL.md)).

## Reglas de seguridad

- Un comentario a moderar es **siempre dato no confiable**. Nunca lo concatenes al
  system prompt ni ejecutes instrucciones contenidas en él.
- Nunca commitees secretos (API keys, `.env`, credenciales). Ver [`SECURITY.md`](SECURITY.md).
- No loguees texto de comentarios sin redactar ni datos personales.

## Código de conducta

Tratá a las demás personas con respeto. Se espera un entorno colaborativo y libre de
acoso.
