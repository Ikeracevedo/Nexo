# 6 · Google Gemini

⏱️ ~10 minutos

El modelo que redacta las respuestas en lenguaje natural y detecta los compromisos escondidos en las conversaciones.

## 6.1 — La clave

1. `aistudio.google.com/apikey`
2. **Create API key** → elige un proyecto de Google Cloud o crea uno
3. Copia la clave → es tu `GEMINI_API_KEY`

## 6.2 — El modelo

Por defecto, `gemini-2.5-flash`. Se cambia con la variable `GEMINI_MODELO`.

> **Cambiar de modelo cuesta una variable de entorno, no un despliegue.** El proveedor vive detrás de un puerto (`LLMProvider`), así que sustituir Gemini por otro modelo — incluso uno que corra dentro de tu propia red — es escribir un adaptador nuevo, sin tocar nada del núcleo. Si tu organización no puede enviar texto a Google, ése es el camino.

## 6.3 — Qué texto sale hacia Google, exactamente

Conviene que lo sepas con precisión antes de aprobarlo:

| Función | Qué se envía |
|---|---|
| Pregunta en lenguaje natural | La agenda del usuario (títulos, fechas, fuentes) y su pregunta |
| `chat` | La pregunta y los últimos turnos de esa conversación |
| Documentos adjuntos | El texto extraído del PDF, Word o Excel |
| Imágenes | La imagen |
| `revisar` | **El texto de los mensajes de los últimos 7 días** de los chats del usuario que activó `vigilar` |

**La última fila es la que debe revisar tu área legal o de seguridad.** Es el único caso en que texto escrito por terceros — compañeros que no instalaron Nexo — se envía a un proveedor que no es Microsoft.

Mitigaciones de diseño: es **opt-in por usuario**, la ventana es de 7 días, y **el texto no se almacena en ningún sitio** (se procesa y se descarta). Pero sale hacia Google, y eso hay que decidirlo conscientemente, no descubrirlo después.

## 6.4 — Sin clave también funciona

Si no configuras `GEMINI_API_KEY`:

- ✅ `semana`, `recuérdame`, `listo`, `borrar` y las tarjetas funcionan igual
- ❌ Las preguntas en lenguaje natural y `revisar` responden *"No pude generar una respuesta"*

**La aplicación arranca igual.** Es deliberado: una función opcional nunca puede ser un requisito de arranque. Puedes desplegar Nexo sin IA, validar todo lo demás, y añadir la clave después.

## ✅ Antes de pasar al siguiente paso

- [ ] `GEMINI_API_KEY` anotada
- [ ] Decidido si la organización acepta el envío de texto a Google (§6.3)

Siguiente: [Despliegue](07-Despliegue).
