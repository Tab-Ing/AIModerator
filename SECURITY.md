# Política de seguridad

## Reporte de vulnerabilidades

Si encontrás una vulnerabilidad de seguridad, **no abras un issue público**. Escribí a:

- Email: `seguridad@aimoderator.example` *(reemplazar por el correo real)*

Incluí pasos para reproducirla, impacto potencial y, si es posible, una propuesta de
solución. Intentaremos responder en un plazo de 72 horas.

## Alcance relevante

AIModerator procesa texto no confiable de terceros (comentarios de redes sociales).
Las áreas de mayor riesgo son:

- **Prompt injection / jailbreak** en el texto de los comentarios.
- Fuga de secretos o del system prompt a través de salidas del modelo.
- Acceso cruzado entre tenants (aislamiento multi-tenant).
- Manejo de API keys y datos personales de los comentaristas.

## Principios de diseño

1. El comentario se trata **siempre** como dato no confiable; nunca como instrucción.
2. Separación estructural entre datos y prompts; sin interpolación directa.
3. Validación estricta de las salidas (esquema tipado) y descarte de respuestas inválidas.
4. Nunca se ejecutan acciones ni herramientas sugeridas por el texto del comentario.
5. Minimización y redacción de datos personales; el texto se guarda hasheado/redactado.
6. Las API keys se almacenan hasheadas con `AIMODERATOR_SECRET_KEY` como pepper.

## Versiones soportadas

Al estar en fase alfa, solo la rama `main` recibe correcciones de seguridad.
