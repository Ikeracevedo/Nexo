# Política de Privacidad — Brújula

**Última actualización:** 9 de octubre de 2026

Brújula es una aplicación desarrollada como proyecto académico (Proyecto en TIC 1, Universidad
Pontificia Bolivariana) que se integra con Microsoft Teams para ayudar a estudiantes a consolidar,
en un solo lugar, sus pendientes académicos: eventos de calendario, tareas y compromisos de equipo.

Esta política explica, en lenguaje llano, qué datos lee Brújula, para qué los usa, dónde viven y
qué control tiene el usuario sobre ellos.

---

## 1. Qué datos lee Brújula, y por qué

Brújula solicita acceso a tu cuenta de Microsoft mediante los siguientes permisos, **todos de solo
lectura**:

| Permiso técnico (Microsoft Graph) | Qué significa en la práctica | Para qué lo usa Brújula |
|---|---|---|
| `User.Read` | Leer tu nombre y datos básicos de perfil | Saludarte y confirmar que la sesión es tuya |
| `Calendars.Read` | Leer tus eventos de calendario | Mostrarte tus compromisos de la semana |
| `Tasks.Read` | Leer tus tareas (Microsoft To Do / Planner) | Mostrarte tus pendientes junto al calendario |
| `Team.ReadBasic.All` | Ver de qué equipos de Teams eres miembro | Identificar el contexto de tus entregas de equipo |
| `Chat.Read` | Leer tus chats de Teams | Detectar compromisos mencionados en conversaciones |

**No existe ningún permiso de escritura.** Brújula no puede crear, modificar ni borrar nada en tu
calendario, tus tareas, tus equipos ni tus chats — solo puede leerlos. Tampoco puede ver datos de
otros usuarios de tu organización: solo ve lo que tú, con tu propia cuenta, puedes ver.

## 2. Cómo se obtiene el acceso

Brújula usa el flujo de **autorización delegada** de Microsoft (OAuth 2.0). Esto quiere decir:

- Tú das tu consentimiento explícito, una sola vez, a través de la pantalla oficial de Microsoft —
  nunca a través de un formulario propio de Brújula.
- Brújula actúa **como tú y con tus permisos**, nunca con permisos elevados sobre tu organización.
- Puedes revocar el acceso en cualquier momento escribiendo `desconectar` en el chat, o desde
  [myaccount.microsoft.com](https://myaccount.microsoft.com) → Aplicaciones conectadas.

## 3. Dónde viven tus credenciales y tokens

**Brújula nunca ve ni almacena tu contraseña.** El inicio de sesión ocurre por completo dentro de
la pantalla de Microsoft; Brújula nunca la observa.

Los tokens de acceso y de renovación (*refresh tokens*) son gestionados por el **Bot Framework
Token Service** de Microsoft, no por la infraestructura de Brújula. En la práctica:

- Brújula pide un token vigente al servicio de Microsoft en cada operación que necesita hacer.
- Brújula no guarda esos tokens en ninguna base de datos propia.
- Si revocas el acceso, el siguiente intento de lectura falla de inmediato y Brújula te lo informa
  con claridad, sin fingir que no tienes pendientes.

## 4. Qué pasa si algo falla

Si una fuente de datos (por ejemplo, tu calendario) no puede consultarse — porque el permiso fue
revocado, porque hubo un error de conexión, o porque el servicio de Microsoft no respondió — Brújula
**nunca lo interpreta como "no tienes pendientes"**. Te informa explícitamente cuál fuente falló,
y te muestra igualmente los datos de las fuentes que sí respondieron.

El chat general funciona por separado de la agenda. Si MongoDB no responde,
el chat puede contestar, pero indica que no pudo guardar memoria de esa respuesta.

## 5. Datos guardados y uso de Gemini

- Los pendientes creados con `recuérdame` se guardan en MongoDB Atlas con el
  identificador de usuario de Microsoft, título, fecha opcional y estado. No
  se copian allí las tareas ni los eventos consultados desde Microsoft Graph.
- El modo `chat` guarda en MongoDB los últimos 40 turnos breves de cada usuario
  y conversación. Los documentos caducan tras 30 días sin actividad. `olvidar`
  borra el historial de quien lo escribe en esa conversación. Si MongoDB no
  está configurado, la memoria queda solo en el proceso y desaparece al
  reiniciarlo.
- Las imágenes enviadas al chat se descargan temporalmente desde Teams y se
  envían a Gemini para producir la respuesta. No se guardan los bytes de la
  imagen en MongoDB; en la memoria solo queda su nombre.
- Las preguntas sobre la agenda envían a Gemini el texto de los pendientes
  consultados y la pregunta. El modo `chat` envía el mensaje, el historial
  breve y las imágenes adjuntas a Gemini. Google procesa esos datos como
  proveedor externo del modelo.
- `desconectar` revoca la sesión de Microsoft, pero no elimina los pendientes
  propios ni el historial de chat. Para pedir el borrado de pendientes propios,
  contacta al desarrollador indicado al final de esta política.

## 6. Qué no hace Brújula

- No vende tus datos ni los usa con fines publicitarios.
- No mantiene una copia permanente de tus eventos o tareas de Microsoft Graph.
- No registra el contenido de tus eventos, tareas o chats en archivos de registro (*logs*). Los
  logs técnicos solo contienen información operativa (por ejemplo, que una consulta a Graph
  devolvió un error 403), nunca el contenido de tus datos ni tus credenciales.

## 7. Tus derechos

Como usuario, en cualquier momento puedes:

- Revocar el acceso de Brújula a tu cuenta (comando `desconectar`, o desde tu cuenta de Microsoft).
- Preguntar qué fuentes están conectadas realmente (comando `estado`).
- Solicitar información sobre qué datos ha leído Brújula, escribiendo al contacto indicado abajo.
- Borrar el historial del chat con `olvidar` y solicitar el borrado de pendientes propios al contacto.

## 8. Naturaleza académica del proyecto

Brújula es un proyecto desarrollado en el marco de una asignatura universitaria (Proyecto en TIC 1,
UPB). No es un producto comercial en operación permanente. Esta política se mantiene vigente
mientras el proyecto esté activo y se actualizará si su alcance cambia.

## 9. Contacto

Para preguntas sobre esta política o sobre tus datos, contacta al desarrollador:

**Iker Acevedo** — [ikeracevedowrk@gmail.com](mailto:ikeracevedowrk@gmail.com)
Repositorio del proyecto: [github.com/Ikeracevedo/brujula-teams](https://github.com/Ikeracevedo/brujula-teams)

---

## 10. Actualización OT-06: vigilancia y precarga

Esta sección prevalece sobre cualquier redacción anterior relativa a tokens de renovación. La
vigilancia de conversaciones está apagada por defecto. Tras `vigilar`, Brújula obtiene un
consentimiento OAuth separado para la precarga y almacena el *refresh token* delegado cifrado con
Fernet en MongoDB Atlas. Nunca almacena contraseñas, tokens en claro ni tokens en logs; el access
token solo existe en memoria durante la consulta.

El worker procesa únicamente usuarios con vigilancia activa, como máximo cada 30 minutos, con una
ventana de 7 días y hasta 300 mensajes. Los cuerpos de Teams se mandan a Gemini solo en memoria y
se descartan al terminar. Se persisten la sugerencia reformulada, su enlace, estado y una huella
técnica de identificadores/fechas, nunca el cuerpo del mensaje ni el prompt. `no vigilar` elimina
el refresh token cifrado y detiene la precarga para ese usuario.
