# Defensa anti-prompt-injection

Un comentario a moderar es **siempre dato no confiable**. Nunca se interpreta como
instrucción ni se ejecuta. Modelo de amenazas alineado con **OWASP LLM01: Prompt
Injection**.

## Amenazas

- **Inyección directa:** el comentario intenta sobrescribir instrucciones
  ("ignorá las reglas anteriores", "SYSTEM: ...", marcadores de rol).
- **Inyección indirecta:** el texto contiene contenido que induce al modelo a cambiar de
  tarea o a filtrar el prompt.
- **Exfiltración:** pedir el system prompt, secretos o configuración interna.
- **Uso de herramientas:** inducir llamadas a funciones/acciones no autorizadas.
- **Ofuscación:** base64, homoglifos, unicode zero-width/bidi, separadores raros.

## Capas de defensa

1. **Normalización**
   - Normalización Unicode (NFKC).
   - Eliminación de caracteres de control, zero-width y controles bidireccionales.
   - Colapso de espacios y **límite de longitud**.
2. **Separación estructural**
   - El texto va **siempre** en un campo de datos delimitado y etiquetado como no
     confiable. Nunca se concatena al system prompt.
3. **Detector dedicado**
   - Esquema de prompt injection en Jev AI (clasificación calibrada).
   - Heurísticas: frases conocidas, marcadores de rol, blobs codificados.
   - Opcionalmente, clasificador local especializado.
   - Puede **short-circuit**: bloquear antes de invocar un LLM costoso.
4. **Jerarquía de instrucciones**
   - Prompt endurecido con instrucciones explícitas de tratar el comentario como dato.
   - Sin secretos ni herramientas en el prompt.
5. **Validación estricta de salida**
   - Salidas con **esquema tipado** (Jev) o JSON validado con Pydantic.
   - Se **descarta** cualquier salida inválida; nunca se ejecuta contenido del texto.
6. **Observabilidad y respuesta**
   - Se registra `injection_flag` y la categoría `prompt_injection`.
   - Nunca se loguea el texto crudo del comentario con datos personales (hash/redacción).

## Categorías de moderación

`toxicity`, `harassment`, `hate`, `spam`, `prompt_injection`.

## Corpus de pruebas

`tests/pi_corpus/injections.json` reúne payloads de referencia. Debe crecer con cada
nuevo vector detectado. Los tests verifican que se marquen como
`prompt_injection`/`suspicious` y que los benignos no se bloqueen.

## Reglas para desarrolladores

- Nunca concatenar entrada del usuario al system prompt.
- Nunca ejecutar acciones/tools sugeridas por el comentario.
- Tratar toda salida del modelo como dato a validar, no como instrucción.
- Agregar un test por cada nuevo vector de ataque mitigado.
