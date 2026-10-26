# Nexo — Guía de instalación para el administrador de TI

> **⚠️ BORRADOR — versión 0.1, 8 de septiembre de 2026.**
> Los campos marcados «así» están pendientes y **no se puede enviar a nadie hasta rellenarlos**.
> Las secciones marcadas 🔴 dependen de decisiones que el proyecto aún no ha tomado.
>
> *Nota interna, borrar antes de publicar: este documento es para un cliente. El procedimiento de
> montaje del entorno de desarrollo está en `RUNBOOK-TENANT.md` y no se comparte.*

---

## En 30 segundos

Nexo es un asistente dentro de Microsoft Teams que responde *"¿qué tengo esta semana?"*
reuniendo los pendientes que su gente ya tiene dispersos en Planner, To Do, Calendario y
conversaciones, y devolviéndolos en una sola lista **con enlace a su origen**.

| | |
|---|---|
| **Qué necesita de usted** | Una aprobación de consentimiento y una instalación en Teams. Nada más |
| **Qué instala en su infraestructura** | Nada. Nexo se ejecuta en «‹hosting›», fuera de su tenant |
| **Qué permisos pide** | Cinco, **todos de solo lectura**. Ninguno de escritura |
| **Qué datos ve** | Únicamente los del usuario que inició sesión, y solo lo que ese usuario ya puede ver |
| **Tiempo de instalación** | ~10 minutos |
| **Cómo se revoca** | Un clic, desde su propio portal. Sección 5 |

---

## 1. Qué hace y qué no hace

**Sí:**
- Reúne pendientes de Planner, To Do y Calendario del usuario autenticado.
- Detecta compromisos mencionados en conversaciones y los marca **como inferencias**, con su nivel
  de confianza y un aviso explícito de que deben verificarse.
- Enlaza cada elemento a su origen dentro de Teams.

**No:**
- ❌ No es un asistente de propósito general. Fuera de sus pendientes, declina responder.
- ❌ No lee la organización. Solo lo que el usuario autenticado ya tiene permiso de ver.
- ❌ **No escribe nada.** No crea, no modifica y no borra tareas, eventos ni mensajes.
- ❌ No reemplaza a Planner. Lo unifica con lo que Planner no ve.

---

## 2. Permisos solicitados

Los cinco son **permisos delegados de Microsoft Graph**: Nexo actúa *como el usuario* y con los
permisos del usuario. Nunca por sí misma sobre la organización.

| Permiso | Qué dato lee | Para qué |
|---|---|---|
| `User.Read` | Nombre y correo del usuario que inició sesión | Identificar a quién se responde |
| `Calendars.Read` | Eventos del calendario **del propio usuario** | Mostrar compromisos de la semana |
| `Tasks.Read` | Tareas de To Do y Planner del usuario | Fuente principal de pendientes |
| `Group.Read.All` | Grupos de Microsoft 365 relacionados con Planner | Consultar las tareas de Planner que corresponden al usuario |
| `Chat.Read` | Mensajes de los chats del usuario | Detectar compromisos mencionados en conversación |

### Lo que NO se pide, y es lo importante

**Ningún permiso termina en `ReadWrite`. Ninguno.** Nexo no puede modificar nada en su tenant,
ni aunque quisiera: los permisos que se lo permitirían no están en la solicitud, y añadirlos
requeriría una nueva aprobación suya.

Tampoco se solicita `ChannelMessage.Read.All` — el permiso que daría acceso a los mensajes de los
canales de la organización. Se confirmó (13-sep-2026) que ese permiso es *Protected API* y no se
consigue por el camino normal de esta guía: cuando se necesite, la vía es **RSC** (*Resource-Specific
Consent*), donde el propietario de un equipo concreto autoriza la app solo sobre ese equipo — sin
pasar por usted como administrador del tenant. Se documentará como una decisión suya, equipo por
equipo, cuando esa fuente esté implementada.

> Sobre `Group.Read.All`: el sufijo `.All` exige una revisión explícita del administrador. Nexo lo
> usa para consultar las tareas de Planner asociadas a los grupos de Microsoft 365; no solicita
> permisos de escritura sobre grupos, tareas ni mensajes.

---

## 3. Requisitos previos

- Un tenant de Microsoft 365 con Teams (cualquier plan de empresa o educación).
- Un usuario con rol **Administrador global** o **Administrador de aplicaciones en la nube**.
- Permitir la carga de aplicaciones personalizadas, **o** publicar Nexo en su catálogo interno.
  Sección 4.2.

---

## 4. Instalación

### 4.1 — Aprobar el consentimiento (una vez, para toda la organización)

Abra esta dirección con su cuenta de administrador, reemplazando `{su-tenant}` por el dominio o el
identificador de su organización:

```
https://login.microsoftonline.com/{su-tenant}/adminconsent?client_id=«CLIENT_ID_DE_PRODUCCION»
```

Verá la lista exacta de permisos de la sección 2. Revísela antes de aprobar: **lo que aparece en
esa pantalla es todo lo que Nexo puede hacer.** Si aparece algo distinto de esos cinco permisos
de lectura, **no apruebe y avísenos** — significaría que está usando un enlace que no es el nuestro.

> 🔴 **Pendiente del proveedor:** el `CLIENT_ID` de la aplicación de producción. El actual pertenece
> al entorno de desarrollo y **no debe distribuirse**.

### 4.2 — Instalar la aplicación en Teams

**Opción A — catálogo de la organización (recomendada).**
Centro de administración de Teams → *Aplicaciones de Teams* → **Administrar aplicaciones** →
*Cargar nueva aplicación* → seleccione el paquete `nexo-teams.zip` que le entregamos.
Desde ahí puede asignar quién ve la app mediante directivas de permisos.

**Opción B — carga individual.** Si su organización permite cargar apps personalizadas, cada
usuario puede instalarla desde *Aplicaciones → Administrar tus aplicaciones → Cargar una aplicación
personalizada*.

### 4.3 — Comprobar que funciona

Abra un chat con **Nexo** y escriba `ayuda`. Debe responder con la lista de comandos
disponibles. Después, `semana`.

**En el primer uso, cada usuario verá una pantalla de inicio de sesión de Microsoft.** Es esperado:
el consentimiento de administrador autoriza a la aplicación, pero cada usuario sigue autenticándose
con su propia cuenta. Nexo nunca ve ni almacena contraseñas.

---

## 5. Cómo revocar el acceso

En cualquier momento y sin avisarnos:

**Portal de Microsoft Entra** → *Aplicaciones empresariales* → buscar **Nexo** →
**Propiedades** → *Eliminar*.

El acceso se corta de inmediato. Los tokens emitidos dejan de renovarse y los existentes caducan en
menos de una hora.

Para desactivarla sin eliminarla: en la misma pantalla, *Propiedades* → **¿Habilitado para que los
usuarios inicien sesión?** → **No**.

> Incluimos esto en la portada de la guía y no en un anexo a propósito. **Un administrador confía en
> lo que puede desinstalar**, y una app que esconde cómo se quita da exactamente la señal contraria.

---

## 6. Tratamiento de datos 🔴

> **Borrador para revisión del administrador.** Antes de una instalación de
> cliente, confirmar la región de Atlas y las condiciones de tratamiento de
> datos vigentes de Google. El despliegue académico registrado en la bitácora
> usa una VM de Azure en México Central.

| Pregunta | Respuesta |
|---|---|
| ¿Dónde se ejecuta Nexo? | Despliegue académico: Azure VM en México Central. Confirmar la región del despliegue de cada cliente. |
| ¿Qué se almacena? | En MongoDB Atlas: pendientes creados con `recuérdame`, hasta 40 turnos breves por usuario y conversación del modo `chat`, sugerencias detectadas y un refresh token cifrado únicamente para usuarios que activan `vigilar`. No se guardan copias de eventos, tareas ni cuerpos de mensajes de Teams. |
| ¿Durante cuánto tiempo? | La memoria de chat caduca tras 30 días sin actividad y puede borrarse con `olvidar`. Los pendientes propios permanecen hasta que se solicite su eliminación. |
| ¿Se almacenan credenciales? | **No.** Nunca se almacenan contraseñas de usuario |
| ¿Cómo se guardan los tokens? | Para `vigilar`, Nexo conserva un refresh token delegado cifrado con Fernet. El access token solo existe en memoria y `no vigilar` elimina el refresh token cifrado. |
| ¿Se usan los datos para entrenar modelos? | La aplicación no entrena modelos. Las condiciones de uso de datos de Gemini deben revisarse con Google antes de aprobar un tenant cliente. |
| ¿Qué proveedor de IA procesa el texto? | Google Gemini procesa preguntas sobre la agenda, chat general e imágenes. Confirmar región y retención contractual antes de instalar en un cliente. |
| ¿Hay subencargados de tratamiento? | Microsoft, MongoDB Atlas y Google intervienen en los flujos descritos. Revisar los acuerdos de tratamiento aplicables. |

`desconectar` revoca la sesión de Microsoft; no borra los pendientes propios ni
el historial de chat. `olvidar` borra solo el historial del usuario en esa
conversación. El contacto de la sección 9 tramita solicitudes sobre pendientes
propios.

---

## 7. Estado de verificación del editor 🔴

**Nexo no cuenta todavía con el distintivo *Verified Publisher* de Microsoft.**

Consecuencias concretas para usted:

1. En la pantalla de consentimiento aparecerá un aviso de que el editor no está verificado.
2. Si su tenant tiene deshabilitado el consentimiento de usuario —una configuración común y
   recomendable—, **solo un administrador podrá autorizar la aplicación**. Los usuarios no podrán
   hacerlo por su cuenta.

Lo decimos en la guía en lugar de dejar que lo descubra en la pantalla de aprobación. *Pendiente
del proveedor: alta en el Microsoft Partner Network y solicitud de verificación.*

---

## 8. Preguntas frecuentes

**¿Puede un usuario ver los pendientes de otro?**
No. Cada respuesta se construye con el token del usuario que pregunta, y ese token solo abre lo que
ese usuario ya puede abrir. No existe ninguna ruta en la que Nexo consulte datos de un usuario
distinto del que hizo la petición.

**¿Y si el modelo se inventa una fecha de entrega?**
Nexo distingue explícitamente un **hecho** de una **inferencia**. Lo que viene de Planner, To Do
o Calendario se muestra como confirmado. Lo que se deduce de una conversación se muestra en otro
color, con su porcentaje de confianza y el aviso *"Nexo no confirma este pendiente. Verifícalo
en el origen."* Todo elemento, sin excepción, enlaza a su fuente.

**¿Qué pasa si Nexo no puede consultar una de las fuentes?**
Lo dice. Si Planner no responde, la respuesta incluye *"No pude consultar: Planner — esta lista
está incompleta."* **Nunca presenta un fallo como ausencia de pendientes**, porque un usuario que
confía en un "no tienes nada" equivocado pierde una entrega.

**¿Qué diferencia hay con Microsoft Copilot?**
Copilot requiere licencia adicional y es un asistente de propósito general. Nexo hace una sola
cosa —unificar pendientes dispersos con trazabilidad obligatoria— y funciona sin licencias de
Copilot.

**¿Podemos probarla en un grupo reducido antes de desplegarla?**
Sí. En el paso 4.2, opción A, use las directivas de permisos de aplicaciones de Teams para
asignarla solo a un grupo piloto.

**¿Qué pasa si dejamos de usarla?**
Sección 5. La eliminación es inmediata y no requiere contactarnos.

---

## 9. Contacto

| | |
|---|---|
| Responsable | «nombre» |
| Correo de soporte | «correo» |
| Repositorio del proyecto | «URL» |
| Aviso de privacidad | «URL» — 🔴 obligatoria para publicar en Teams |
| Términos de uso | «URL» — 🔴 obligatoria para publicar en Teams |

---

### Anexo — Lista de comprobación del administrador

- [ ] Revisé los cinco permisos y confirmé que ninguno es de escritura
- [ ] Aprobé el consentimiento de administrador
- [ ] Cargué el paquete en el catálogo de la organización
- [ ] Asigné la app al grupo piloto
- [ ] Probé `ayuda` y `semana` con una cuenta real
- [ ] Verifiqué que el procedimiento de revocación funciona **antes** del despliegue general
