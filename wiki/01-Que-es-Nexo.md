# 1 · Qué es Nexo y qué hace con tus datos

Antes de configurar nada, conviene entender qué estás instalando. Si eres quien tiene que **aprobar** esta aplicación en la organización, esta página es la que te interesa.

## El problema que resuelve

Una persona dentro de Microsoft 365 tiene sus compromisos repartidos:

- Un evento en el **calendario de Outlook**
- Una tarea en **Microsoft To Do**
- Una tarjeta en un plan de **Planner**
- Y una frase suelta en un chat: *"listo, mañana te paso el informe"*

Las tres primeras exigen que alguien las haya anotado. **La cuarta es la que de verdad se olvida.**

Nexo responde a *"¿qué tengo esta semana?"* unificando las cuatro, dentro de Teams, sin que nadie cambie de herramienta.

## Qué permisos pide, y qué significan en la práctica

Todos son **delegados** y **de solo lectura**. Delegado quiere decir que Nexo actúa **con el token de la persona**: no puede ver nada que esa persona no pueda ver ya abriendo Outlook.

| Permiso | Qué permite leer | Por qué hace falta |
|---|---|---|
| `User.Read` | Nombre y correo del usuario que inicia sesión | Saber de quién son los datos |
| `Calendars.Read` | Eventos del calendario propio | Las reuniones y eventos de la semana |
| `Tasks.Read` | Tareas de To Do y de Planner | Las dos fuentes de tareas, con un solo permiso |
| `Chat.ReadBasic` | La lista de chats del usuario | Saber qué conversaciones existen |
| `Chat.Read` | Los mensajes de esos chats | Detectar compromisos no anotados — **solo si el usuario lo activa** |
| `Group.Read.All` | Grupos a los que pertenece | Resolver los planes de Planner, que viven en grupos de M365 |
| `offline_access` | Renovar el acceso sin volver a pedir login | Que el usuario no tenga que reconectarse cada hora |

### Lo que NO se pide, y es lo importante

- ❌ **Ningún permiso de escritura.** Nexo no puede crear, modificar ni borrar nada en Microsoft 365.
- ❌ **Ningún permiso de aplicación** sobre la organización. No existe un modo en el que Nexo lea los datos de toda la empresa.
- ❌ **Ningún acceso a correo.** No se pide `Mail.Read`.
- ❌ **Ningún acceso a archivos.** No se pide `Files.Read`.

> `Group.Read.All` es el único permiso de la lista con un nombre alarmante. Lee **la pertenencia a grupos**, no su contenido, y es un requisito de la API de Planner. Es también el motivo por el que el consentimiento lo tiene que dar un administrador.

## La lectura de conversaciones, en detalle

Es la función más potente y la más sensible. Está diseñada con seis reglas:

1. **Apagada por defecto.** Cada usuario la enciende escribiendo `vigilar` y la apaga con `no vigilar`.
2. **Ventana de 7 días.** Nunca el histórico completo.
3. **El texto de los mensajes no se almacena.** Se procesa en memoria y se descarta. En la base de datos solo queda el pendiente propuesto y el enlace al mensaje: **el texto original se queda en Teams**, bajo las políticas de tu tenant.
4. **Lo detectado es una sugerencia, no un pendiente.** Va a una bandeja aparte hasta que la persona la acepta.
5. **Trazabilidad siempre.** Cada sugerencia enlaza al mensaje exacto del que salió.
6. **Los mensajes se tratan como datos no confiables.** El modelo solo puede devolver una estructura de datos cerrada, nunca texto libre — así, un mensaje malicioso de un tercero no puede darle instrucciones al sistema.

## Qué se almacena, dónde y cuánto tiempo

En **tu** clúster de MongoDB, bajo **tu** control:

| Colección | Contenido | Retención |
|---|---|---|
| `pendientes` | Pendientes creados por el usuario con `recuérdame` | Hasta que los borre |
| `sugerencias` | Compromisos propuestos + enlace al mensaje | Hasta aceptarlos o descartarlos |
| `preferencias` | Si cada usuario activó la vigilancia | Mientras use Nexo |
| `credenciales_graph` | *Refresh tokens* **cifrados con Fernet** | Hasta que el usuario escriba `desconectar` |
| `estados_oauth` | Estados temporales del login | 10 minutos |
| `estado_precarga` | Marca de cuándo se actualizó cada usuario | Mientras use Nexo |

**Nunca se almacenan:** contraseñas, cuerpos de mensajes de Teams, copias de eventos o tareas de Microsoft, ni bytes de las imágenes enviadas al chat.

## Terceros que intervienen

| Proveedor | Qué procesa |
|---|---|
| **Microsoft** | Identidad y los datos de origen (ya es tu proveedor) |
| **MongoDB Atlas** | Almacena lo de la tabla de arriba, en la región que elijas |
| **Google (Gemini)** | Procesa el texto de las preguntas y de los mensajes analizados para redactar respuestas y detectar compromisos |

> **Revisa las condiciones de tratamiento de datos de Google antes de aprobar Nexo para datos sensibles.** Es el único punto en el que texto de tu organización sale hacia un tercero que no es Microsoft, y debe ser una decisión consciente de tu área legal o de seguridad.

Siguiente: [Requisitos previos](02-Requisitos-previos).
