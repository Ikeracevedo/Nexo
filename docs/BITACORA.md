# BITÁCORA DEL PROYECTO

> Registro vivo. Se actualiza al cerrar cada Orden de Trabajo.
> Leer junto con `PLAN-MAESTRO.md` al inicio de cada chat.

**Estado actual:** **F3 — Graph delegado** (30 sep–14 oct); preparación de F4
**OT activa:** **Validación real de OT-05 y F4 web responsive**
**OT-04 y OT-04B:** ✅ CERRADAS (16-sep-2026). Datos reales y despliegue en Azure VM exitosos.
**OT-03A:** ✅ CERRADA (13-sep-2026)
**OT-02B:** ✅ CERRADA (8-sep-2026), auditada ejecutando la suite. PR #1 mergeada
**OT-02A:** 98% — bot vivo respondiendo en Teams contra el código permanente (`app/main.py`, no el spike).
**OT-01:** ✅ CERRADA (23-ago-2026)
**Repositorio:** `brujula-teams` (público) — `github.com/Ikeracevedo/brujula-teams`
**Nombre del proyecto:** **Brújula**
**⏰ ENTREGA FINAL: 28 DE OCTUBRE DE 2026.** Checkpoints: 16 sep · 30 sep · 14 oct · 28 oct
**Documentos vivos:** `PLAN-COMPLETO.md` · `BITACORA.md` · `RUNBOOK-TENANT.md` · `GUIA-INSTALACION-TI.md` (borrador) · `GUIA-OPERACION.md`
**Última actualización:** 9 de octubre de 2026 (integración PR #8 desplegada y verificada).

---

## Sesión del 9-oct-2026 — Sincronización e integración del equipo

- `main` local se actualizó por avance rápido hasta `2ae57f0` (PR #7). La rama
  `feat/gemini-integrado` ya aportó To Do, Planner, MongoDB para pendientes
  propios y `recuérdame`; se comprobaron 143 pruebas, Ruff y mypy en verde
  antes de integrar.
- Julián trabajó en `feature/gemini` → `feature/memoria-conversacion` →
  `feature/adjuntos`. Estas ramas parten de `42a70cd`; mezclarlas completas
  con `main` borraría los adaptadores y pruebas añadidos después. Se tomó
  `feature/adjuntos` como referencia para portar sus capacidades.
- La integración se preparó en `feat/integracion-equipo`: `chat <pregunta>`
  ofrece conversación general con memoria, las imágenes de Teams se envían
  a Gemini y `olvidar` borra el historial del usuario en esa conversación.
  `semana`, las preguntas sobre pendientes y `recuérdame` conservan su flujo.
- La memoria se aisló por **usuario y conversación**, porque el ID de una
  conversación de Teams puede ser compartido. En Mongo se guarda solo texto
  breve (máximo 40 turnos) con caducidad tras 30 días; las imágenes no se
  persisten. La descarga solo acepta HTTPS en hosts de Teams/Bot Framework
  y rechaza redirecciones para evitar SSRF o fuga del token del bot.
- Se corrigieron `PRIVACIDAD.md`, la guía de TI y el README para declarar
  MongoDB, Gemini y el alcance real de cada modo. La verificación en Teams,
  Azure, Atlas y el enlace de Planner/To Do sigue pendiente; los tests sin red
  no sustituyen esa prueba. La detección de pendientes desde mensajes de
  canal permanece como OT-06 y la web responsive sigue en F4.
- **Cierre de integración:** PR #8 fusionada a `main` en `e6d32b9`. GitHub
  Actions ejecutó `calidad` y `desplegar` con resultado **success**; el
  endpoint público `https://brujula-teams.duckdns.org/health` respondió 200
  con `entorno=production`. En un venv recreado desde cero se verificaron
  `ruff check`, `ruff format --check`, `mypy` y **158 pruebas** en verde.
  La primera ejecución del script limpio marcó tres falsos fallos causados
  por un script temporal ajeno al commit y un cambio de rama concurrente;
  se retiró el script y se repitieron las cuatro compuertas en ese mismo
  venv limpio, todas verdes.
- **Límite de la verificación:** el despliegue y `/health` no demuestran que
  `chat`, imágenes, `olvidar`, las cuatro fuentes ni `recuérdame` funcionen
  de punta a punta en Teams con permisos y datos reales. Hay que ejecutar
  esa prueba con el usuario del tenant y registrar el resultado antes de
  declarar OT-05 cerrada.

**Regla general:** una rama antigua que añade capacidades también arrastra
decisiones antiguas. Integrar es portar el comportamiento valioso sobre la
arquitectura vigente y verificar las fronteras de datos; no mezclar el árbol
de archivos completo.

---

## Sesión del 16-sep-2026 — Cierre de OT-04 (Autenticación Delegada) y despliegue OT-04B

### Auditoría de OT-04: ✅ CERRADA
La autenticación delegada de OAuth con Teams y Microsoft Graph se completó con éxito.
- El manifiesto fue corregido (`token.botframework.com` añadido a `validDomains`) permitiendo el flujo de login nativo sin el error genérico "App does not exist".
- El comando `conectar` despliega correctamente el inicio de sesión.
- El comando `semana` devuelve los eventos reales del calendario del usuario.
- El error de `Graph API` al pasar un diccionario en lugar del objeto `RequestConfiguration` requerido por Kiota SDK fue detectado gracias a un `logger.exception` temporal. Fue corregido y probado con éxito.
- **Triunfo arquitectónico comprobado:** Cuando Graph falló por el error de parámetros, la aplicación *no se cayó* con un HTTP 500. El adaptador cumplió su contrato devolviendo un `FuenteNoDisponibleError`, y la capa de servicios respondió grácilmente indicando "No pude consultar: calendario" y mostrando 0 eventos. ¡La arquitectura hexagonal protegió al usuario final del crash!
- El test de `graph_calendario` fue actualizado para reflejar la aserción sobre `RequestConfiguration`.
- `ruff` previno exitosamente un commit sucio (espacios en blanco en línea vacía) gracias al pipeline de CI, validando la importancia de la Fase 7.1.

### OT-04B: Despliegue en Azure VM — ✅ CERRADA
- El backend corre en un contenedor Docker (`ghcr.io/ikeracevedo/brujula-teams:latest`) en una Azure VM (Ubuntu, `Standard_B2s_v2`, `mexicocentral`).
- El tráfico HTTPS es gestionado por DuckDNS y Caddy.
- El pipeline de GitHub Actions despliega automáticamente tras cada push a `main`.
- **Lección operativa clave:** `docker compose up -d` no recrea un contenedor automáticamente cuando el archivo `.env` cambia en el host sin que lo sepas. Se debió ejecutar manualmente para inyectar el nuevo `TEAMS_BOT_ID` (el Single Tenant validado en 15-sep) en memoria del contenedor, resolviendo el error `Audience doesn't match` y un `401 Unauthorized` desde Bot Framework.

---

## Sesión del 13-sep-2026 (noche) — OT-03A auditada, runbook cerrado y tablero con fechas

### Auditoría de OT-03A: ✅ CERRADA

Se trajo el repo a un entorno limpio y se ejecutó. No se leyó: se corrió.

| Comprobación | Resultado |
|---|---|
| `pytest` | ✅ **57 verdes** |
| `mypy --strict` | ✅ Success, 29 archivos |
| `ruff check` / `ruff format --check` | ⚠️ **1 error** — `import logging` fuera de orden en `app/main.py` |
| Bot en Teams real | ✅ Verificado en `Brujula-resumen.semanal.png`: *"Tu semana — 4 pendientes, 3 confirmados, 1 inferidos"* |
| **4 sabotajes de arquitectura** | ✅ **Los cuatro fallan** con el mensaje correcto |

**Los cuatro guardarraíles del ADR-004 funcionan.** No son decorativos.

**Reconocimiento registrado:** la **prueba de reinicio completo de la máquina** siguiendo la propia
`GUIA-OPERACION.md` es *probar* un runbook, no escribirlo — casi nadie lo hace, y encontró un
hallazgo real (`$env:Path` con `+=` no sobrevive un reinicio). Y **auditar el tablero contra
criterios literales sin mover nada a Done** es disciplina poco común: un tablero que miente es peor
que no tener tablero.

### Respuesta del docente — R10 se degrada

**Registrado literalmente como lo reportó el tech lead (13-sep):** *"los criterios de aceptación no
son checklist, los cumplí pero realmente no me detuve a cambiar el texto. Nosotros le explicamos al
docente la forma de trabajar y no hay problemas."*

**R10 pasa de 🟠 a 🟡.** El docente conoce y acepta la forma de trabajo.

> **Salvedad del mentor, registrada:** la respuesta es **verbal y no textual**. El criterio de
> aceptación de esa tarjeta pedía *"respuesta registrada literalmente"* y *"por escrito si es
> posible"*. Con 6 semanas para la entrega y la nota apostada a un solo canal, un correo de dos
> líneas —*"confirmo que el agente en Teams satisface el requisito de implementación responsive"*—
> convierte un acuerdo en evidencia. **Recomendación abierta, decisión del tech lead.**

### 🔴 Reglas de agente: reescritas para no contradecir los ADR

**Hallazgo:** `.agents/rules/01-code-standards.md` era el perfil general de Iker y prescribía
**.NET / C# / Angular / AWS / microservicios / serverless**, contradiciendo ADR-001 (Python), ADR-004
(monolito modular, microservicios descartados como YAGNI) y la elección de Azure.

> **El principio, más importante que el caso:** *las reglas de un agente son configuración de
> producción.* Si contradicen la arquitectura del repo, **el agente no se equivoca: obedece.** Y el
> daño es peor que el de un humano confundido, porque el agente no duda — aplica la regla con
> confianza y en muchos archivos a la vez.

**Corrección de la recomendación del mentor.** La propuesta original (OT-04, F0.3) era crear un
`05-brujula-arquitectura.md` **con precedencia** sobre el 01. **Era peor solución:** dos documentos
que se contradicen con un árbitro siguen siendo dos documentos que se contradicen, y tarde o
temprano alguien lee el equivocado. *Las reglas de precedencia son un olor a diseño; lo correcto es
que no haya contradicción.*

**Con autorización del tech lead, se reescribieron los cinco archivos** (13-sep):

| Archivo | Qué cambió |
|---|---|
| `00-identity.md` | Slack → chat y bitácora. Añadida la regla *verificar, no predecir* |
| `01-code-standards.md` | .NET/Angular/AWS/microservicios → **el stack real**, la arquitectura hexagonal con sus reglas verificadas, y las reglas de producto como restricciones de código |
| `02-security.md` | **Fuera los IDs de cuentas AWS del trabajo.** Ahora: secretos, mínimo privilegio en Graph, aislamiento entre usuarios (OWASP #1), honestidad |
| `03-workflow.md` | Pipelines a AWS → ciclo de OT y Definition of Done reales |
| `04-autonomy-levels.md` | Aprobaciones por Slack → en el chat; lista concreta de qué es 🔴 INPUT |

**Buena decisión previa del tech lead, verificada:** `.agents`, `CLAUDE.md` y `GEMINI.md` **están en
`.gitignore`**, así que los identificadores de cuentas AWS del empleador **nunca estuvieron en el
repositorio público**. El problema era de contexto del agente, no de exposición.

### `RUNBOOK-TENANT.md` completado — se usa mañana

**P6, P7 y P8 llevaban desde el 8-sep marcados ⏳.** Se rellenaron con los datos reales de la
ejecución de OT-03A, y se añadió un paso nuevo:

- **P6** — recurso **Azure Bot** (no registro suelto): tier **F0** gratuito, tipo **Multi Tenant**,
  canal de Teams. Con la advertencia de que el secreto del bot **vence por separado** del de Entra.
- **P6b — NUEVO.** Conexión OAuth del bot. `Tenant ID = common`, los 5 scopes, redirect URI de
  `token.botframework.com`. **Es la única sección del runbook escrita desde la documentación y no
  desde la experiencia**, y queda marcada como tal.
- **P7** — túnel persistente `brujula-dev`, con el hallazgo del `$env:Path`. Descubrimiento útil:
  **el túnel NO se pierde al cambiar de tenant** (está creado con cuenta personal).
- **P8** — el `botId` es **el único campo que rompe el paquete** al cambiar de tenant, y falla en
  silencio: la app instala sin error y el bot no responde nunca.
- **Sección nueva "🗓️ Día de la reconstrucción"** con el orden del día, los tres errores más caros
  y la verificación P10.3.

> **Patrón detectado y escrito:** la decisión "multiinquilino" hay que tomarla **tres veces** —
> tipo de cuenta de Entra (P3), *Type of App* del Azure Bot (P6) y `Tenant ID` de la conexión OAuth
> (P6b). Acertar en dos y fallar en una deja el sistema roto de una forma que solo se descubre
> cuando un usuario externo intenta entrar.

### Decisión: la reconstrucción del tenant se hace el **14-sep**, antes de OT-04

Se incorpora a `OT-04.md` como **Fase −1**, porque la conexión OAuth (F1) se configura sobre el
registro de bot del tenant **nuevo**: hacerla en el viejo sería trabajo tirado.

**La reconstrucción es además la validación empírica del runbook** (P10.3): si el sistema arranca
cambiando solo el `.env`, queda demostrado el requisito de OT-01 — *cambiar de tenant cuesta solo
variables de entorno*. Si no arranca, se acaba de localizar un identificador escrito a fuego en el
código.

### Tablero de Trello: 30 tarjetas fechadas

Alineadas con los checkpoints del curso (hora de cierre: 18:00 Bogotá):

| Fecha | Qué | Cuántas |
|---|---|---|
| **16-sep** | OT-04 — autenticación delegada y calendario real | 9 |
| **30-sep** | OT-05 — Planner, To Do, unificación, hito HU-07.9 | 8 |
| **14-oct** | OT-06 — LLM, Mongo, mensajes de canal (RSC) | 7 |
| **21-oct** | Diagramas de rúbrica + documento de arquitectura + **despliegue público** | 5 |
| **27-oct** | Ensayo de sustentación | 1 |

**Sin fecha, a propósito:** `🔭 IDEAS A LARGO PLAZO` — es backlog parqueado, no trabajo comprometido.

> **Por qué los diagramas y el despliegue van el 21 y no el 28:** son requisitos literales de la
> rúbrica y el despliegue es lo que hace que la demo exista sin el portátil de Iker encendido.
> Ponerlos la víspera es apostar la nota a que nada salga mal el último día.

**Solo se asignaron fechas. No se movió ninguna tarjeta de lista** — eso lo hace el tech lead.

### ⚠️ Dos tarjetas con criterios de aceptación obsoletos

El hallazgo del 13-sep (el SDK resuelve la autenticación) **invalida criterios ya escritos**:

| Tarjeta | Criterio obsoleto | Realidad |
|---|---|---|
| **HU-03.2** | *"Flujo OAuth 2.0 authorization code + PKCE implementado"*, *"el `state` de OAuth se valida"* | No se implementa a mano: `ctx.sign_in()` del SDK lo hace |
| **HU-03.3** | *"Los refresh tokens se almacenan cifrados en reposo"*, *"la clave de cifrado vive en variable de entorno"* | **No hay refresh tokens que cifrar.** Los custodia el Bot Framework Token Service |

> **Esto es bueno, no malo, y hay que saber contarlo.** El ADR-002 pedía *"cero credenciales
> almacenadas; solo tokens de corta vida y refresh tokens cifrados"*. La realidad quedó **más
> fuerte que la promesa**: ni siquiera hay refresh tokens que cifrar. Ante *"¿dónde guardan los
> tokens?"*, la respuesta es *"en ningún sitio: los custodia el servicio de identidad de Microsoft;
> nosotros pedimos uno vigente por petición"*.
>
> **Pendiente del tech lead:** reescribir los criterios de esas dos tarjetas. Un criterio de
> aceptación que ya no se puede cumplir porque el mundo cambió no se marca como hecho: se corrige.

### Deuda que sigue abierta

| # | Qué | Dónde se cierra |
|---|---|---|
| 1 | `ruff check` / `format` en rojo por `app/main.py` | OT-04 F0.1 (`ruff check . --fix`) |
| 2 | `manifest.json` → `developer` sigue en `My App, Inc.` / `example.com` (R16) | OT-04 F0.2 |
| 3 | Faltan 2 de 4 capturas de OT-02A + la de móvil | OT-04 F6 |
| 4 | **No hay CI** — lo exige el propio Definition of Done | OT-04 F7.1 |
| 5 | Bot probado solo en ámbito `personal`, no en `team` ni `groupChat` | OT-04 F6.7 |
| 6 | Trazabilidad probada con 1 fuente de 4; "Ver origen" sin verificar a mano | OT-04 F6.7 |
| 7 | **E2/E3/E4 sin verificar (R8)** | Sin fecha asignada |
| 8 | **Paquetes de Julián y Antonio: cero menciones desde el 23-ago** | Ver abajo |

> **Sobre el punto 8.** El plan asignó a Antonio el **golden dataset** de 40+ preguntas y lo
> calificó como *"el entregable más valioso del proyecto después del núcleo"*, porque es la
> respuesta a la pregunta 3 de sustentación — *"¿cómo mides que responde bien?"*, la que tumba
> proyectos de IA. **Sin golden dataset no hay métrica, y esa pregunta va a llegar.** El plan dice
> que están fuera de la ruta crítica y que el proyecto se sustenta igual; eso sigue siendo cierto
> para el código, no para esa respuesta.

---

## Sesión del 9 al 13-sep-2026 — Reinicio validado + auditoría del tablero de Trello

**Prueba de reinicio completo de la máquina — pasó.** Se apagó el computador y se volvió a levantar
todo desde cero siguiendo `docs/GUIA-OPERACION.md` al pie de la letra: venv, túnel, `uvicorn`,
`/health`, y `ayuda`/`semana` en Teams real. Todo funcionó. Único hallazgo operativo: el
`$env:Path` que agrega `C:\devtunnel` **no sobrevive un reinicio** si se fijó con `$env:Path +=`
(scope de sesión, no persistente). Se corrigió con
`[Environment]::SetEnvironmentVariable("Path", $env:Path + ";C:\devtunnel", "User")`, que si es
permanente — pero solo lo recogen ventanas de terminal **nuevas después de reiniciarla por completo**
(no basta una pestaña nueva en la misma aplicación de terminal). Mientras se confirma que quedó
bien fijado, `C:\devtunnel\devtunnel.exe --version` (ruta completa) es el atajo que no depende de
nada de esto.

**Auditoría del tablero de Trello (`brujula-teams` en Trello) contra su propio Definition of
Done.** Se archivaron las 6 tarjetas introductorias/meta (cómo usar el tablero, leyenda de
etiquetas, Definition of Ready, resumen del MVP, fechas/riesgos, Definition of Done) — quedaban
redundantes con este documento y con `PLAN-COMPLETO.md`. Se archivó `🔭 IDEAS A LARGO PLAZO` — no,
esa se dejó intacta, es backlog parqueado a propósito, no introductoria.

Se revisó cada HU candidata a "Done" contra sus propios criterios de aceptación literales, no de
memoria. **Conclusión: ninguna cumple el 100% todavía**, aunque el avance real es significativo.
Brechas concretas encontradas: HU-04.1 sin probar en scopes `team`/`groupChat` (solo `personal`);
HU-04.3 sin captura de **móvil** (solo escritorio); HU-04.4 sin comando de **estado** que reporte
fuentes conectadas; HU-07.1 sin la excepción `FuenteSinPermiso`; HU-07.6 **sin deduplicación**
(ni empezada); HU-07.7/HU-04.6 sin tests por tipo de fallo de Graph (403/401/timeout/429, porque
no existe adaptador real de Graph todavía); HU-07.8 probado con 1 fuente de las 4 que pide;
HU-02.1 sin el README de una línea por carpeta. **Decisión: no se movió ninguna tarjeta a Done**
hasta resolver con Iker si hay CI configurado y si `feat/canal-teams` ya se mergeó a `main` — el
propio Definition of Done archivado los exige a ambos, sin excepciones.

**Hallazgo de diseño del tablero:** la tarjeta introductoria (antes de archivarla) reveló que el
tablero se diseñó con **5 listas** (Backlog, To do, Doing, QA/Review, Done), pero hoy solo existen
3 (falta Doing y QA/Review). Sin "Doing" no hay dónde poner una HU "a medias" sin forzarla
prematuramente a Done — pendiente de decidir con Iker si se recrean esas dos listas.

**Decisión (13-sep-2026, tech lead): el spike de Teams (`spikes/teams-hello/`) NO se retira todavía.**
Cambia la HU-01.6 original ("borrar el spike"), que se archivó en Trello con la nota de la decisión
nueva escrita en su descripción, en vez de perderse. Razón: el spike sigue vivo y funcional, y no
hay urgencia de limpiarlo mientras el canal permanente (`app/bot/`) siga demostrando ser sólido. Si
más adelante hace falta, se retira con una HU más simple, o se crea un spike nuevo aparte para otra
pregunta — lo que importa ahora es que el canal permanente ya existe y funciona.

**F4.5 cerrada — resultado de Graph Explorer (13-sep-2026):** `GET /teams/{team-id}/channels/
{channel-id}/messages` → **`403 Forbidden`**, permiso exacto `ChannelMessage.Read.All` (*Protected
API*, distinto de `Chat.Read` que sí cubre chats 1-a-1/grupales sin problema). **Decisión
registrada:** la fuente `MENSAJE` se mantiene en el alcance del proyecto, condicionada a
implementar **RSC (Resource-Specific Consent)** cuando se construya su adaptador de Graph
(HU-07.5) — no se descarta ni se limita a chats. Detalle completo (team-id, channel-id, cuerpo del
error) en la tarjeta de Trello HU-01.5 (movida a Done) y en `docs/RUNBOOK-TENANT.md` §10.2.
Actualizados en consecuencia: `RUNBOOK-TENANT.md` §10.2, `GUIA-INSTALACION-TI.md` §2, y
`OT-03A.md` (F4.5 y Compuerta F4 — con la corrección honesta de que solo 2 de las 4 capturas de
F4.4 están listas, no las 4; no se marcó nada como hecho sin verificarlo primero contra la carpeta
`docs/evidencia/` real).

**Auditoría y limpieza del tablero de Trello — continuación:** se archivó la HU-01.6 ("Retirar el
spike") con su descripción reescrita para registrar la decisión nueva antes de archivarla (ver
sesión anterior). Se cerró HU-01.5 con el resultado de Graph de arriba — es la primera HU movida a
Done en esta auditoría, porque a diferencia de las HUs de código, sus criterios de aceptación no
dependen de CI ni de un PR mergeado, solo de haber hecho la medición y registrado la decisión.

**Cierre de sesión (13-sep-2026) — confirmado por Iker con `git log --oneline --graph --decorate
--all`:**

```
*   bac76d8 (HEAD -> main, origin/main, origin/HEAD) fix: logging backend
|\
| * d4b7924 docs: correccion de tabla de integrantes
| * e386500 docs: Eliminacion de emoji innecesario
| * 8f9c157 docs: Correcion del readme
* | 4279236 fix: Mejora en los logs
|/
* 7f32d42 (origin/feat/canal-teams, feat/canal-teams) feat: Creacion Bot funcional...
*   8cbaba2 Merge pull request #1 from Ikeracevedo/feat/esqueleto-hexagonal
```

**Ambas ramas de trabajo (`feat/esqueleto-hexagonal` y `feat/canal-teams`) están mergeadas a
`main`**, y `main` local está sincronizado con `origin/main`. Esto satisface la parte de "PR
mergeado a main" del Definition of Done para las HUs de código que quedaron con ese único punto
pendiente — sigue sin confirmarse si hay **CI** configurado (no se preguntó de nuevo en esta
sesión; queda para la próxima vez que se revise el tablero).

**El fix de logging ya está aplicado — verificado leyendo `app/main.py` en disco, no asumido por
el mensaje del commit:**
```python
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
```
Exactamente la recomendación de la sesión de mentoría anterior (INFO estructurado, no DEBUG
global). **Ítem pendiente cerrado.**

**Decisiones de cierre de Iker para esta sesión:**
- Las 2 capturas que faltan (instalación de la app, mensaje fuera de alcance) **se posponen a
  propósito** — el bot ya está confirmado funcional, no es urgente. Quedan como el único pendiente
  visible de OT-02A/F4.4.
- **No se recrean las listas "Doing" y "QA/Review" en Trello.** El tablero se queda con las 3
  listas actuales (Backlog, To do, Done). Las HUs a medias que se identificaron en la auditoría
  (HU-04.1, HU-04.3, HU-07.1, HU-07.6, HU-07.7, HU-07.8) se quedan en Backlog/To do hasta que
  cumplan sus propios criterios de aceptación completos — no se fuerza un estado intermedio en el
  tablero solo por tenerlo.

**⚠️ Bloqueador conocido de esta sesión:** el bridge de archivos con la máquina de Iker
(`device_bash`) está caído por una actualización de Windows del 8-sep-2026 — problema reportado y
en seguimiento, no achacable al proyecto. `device_list_dir` / `device_stage_files` /
`device_commit_files` siguen funcionando (leer y escribir archivos sigue posible); lo que no
funciona es correr comandos de shell directamente en la máquina de Iker desde el chat. Mientras
dure, cualquier verificación que antes se hacía con un comando se hace pidiéndole a Iker que lo
corra él y pegue el resultado.

---

## Sesión del 8-sep-2026 (noche) — F4 de OT-03A: el bot responde de verdad en Teams

**Bug encontrado y cerrado:** `crear_bot_teams()` no le pasaba `tenant_id` al SDK. El Azure Bot
quedó registrado como *Single Tenant*, pero el SDK asumía multi-tenant por defecto y pedía el token
contra un endpoint genérico que no reconocía la app (`AADSTS700016` / `unauthorized_client`). Se
verificó el nombre exacto del parámetro leyendo el código fuente del paquete instalado
(`microsoft_teams/apps/options.py` — `AppOptions.tenant_id`), no por prueba y error. Fix: pasar
`tenant_id=config.azure_tenant_id` al construir el `App(...)`. Reutiliza el mismo tenant ID que ya
usa la app de Graph — es el mismo tenant físico para las dos identidades.

**Evidencia capturada:** `ayuda` y `semana` (con tarjeta) respondiendo en Teams desde el código
permanente, guardadas en `docs/evidencia/`. Faltan por capturar: instalación de la app y un mensaje
fuera de alcance.

**Pendiente explícito, aplazado a la próxima sesión:** F4.5 — la prueba de Graph Explorer sobre
`GET /teams/{team-id}/channels/{channel-id}/messages` (200 vs 403, para saber si la fuente
`MENSAJE` necesitará RSC). Sigue abierta desde el 2-sep; no bloquea lo demás de F4.

**Logging de diagnóstico:** se añadió temporalmente `logging.basicConfig(level=logging.DEBUG)` en
`app/main.py` para sacar a la luz un traceback que el SDK no propagaba al logger de `uvicorn`. Con
el bug ya resuelto, esa línea debe reemplazarse por una configuración de logging permanente pero a
nivel `INFO` (no `DEBUG` global) — ver razonamiento en la sesión de mentoría de ese mismo día:
un `DEBUG` global es ruido permanente y riesgo de fuga de tokens en texto plano, no una mejora de
observabilidad. Pendiente de aplicar.

**Documentación nueva:** `README.md` reescrito con el estilo del Taller-1 (logo UPB, badges, tabla
de funcionalidades) y `docs/GUIA-OPERACION.md` — manual de arranque día a día (venv, túnel,
`uvicorn`, qué hacer si cambia la URL del túnel).

---

## Tablero de Órdenes de Trabajo

| OT | Fase | Título | Estado |
|---|---|---|---|
| OT-01 | F0 | Reconocimiento de plataforma y primer contacto con Graph | ✅ Cerrada |
| **OT-02A** | F1 | **Spike desechable: ver un bot vivo en Teams** | 🟢 **80% — R4 resuelto; el sideload se cierra en la Fase 4 de OT-03A** |
| **OT-02B** | F1 | **Esqueleto hexagonal + app de Entra ID multiinquilino** | ✅ **CERRADA 8-sep.** Auditada ejecutando: 28 tests, mypy strict, ruff, app multiinquilino, PR #1 mergeada |
| **OT-03A** | F1→F2 | **El canal de Teams sobre el núcleo real** | 🟢 **Orden redactada y verificada — `docs/OT-03A.md`. Lista para ejecutar** |
| OT-03B | F2 | Puerto `LLMProvider` + `FakeLLMProvider` + adaptador Gemini | ⚪ Pendiente |
| OT-04 | F2 | MongoDB Atlas + historial de conversación | ⚪ Pendiente |
| OT-05 | F3 | Adaptadores de Graph: Planner · To Do · Calendario → `Pendiente` | ⚪ Pendiente |

---

## Auditoría del 2-sep-2026 — Hallazgo crítico de planeación

**Se leyó por primera vez `Definicion del curso.pdf`.** Estaba en la carpeta desde el 15 de agosto.
El plan original se construyó **sin leer la rúbrica**. Fallo de planeación del mentor, registrado.

**Consecuencias:**

| Hallazgo | Impacto |
|---|---|
| Entrega final **2 sep – 28 oct**, no noviembre | El plan tenía **6 semanas de más**. Hoja de ruta reescrita a 8 semanas. |
| Entregas parciales **cada dos semanas** | Concepto ausente del plan. Checkpoints incorporados. |
| Rúbrica exige *"responsive (Desk y Mobile)"* | El bot de Teams no lo cumple de forma literal → **ADR-009**, riesgo aceptado con disparador al 30-sep. |
| Exige diagramas de clases, casos de uso y BD | No existían en el plan. Incorporados a F4. |
| E2, E3 y E4 del curso sin verificar | **Deuda abierta.** El tech lead decide postergar la verificación. Se registra como riesgo R8. |

**Lección de proceso (aplica a mentor y a tech lead por igual):**
*antes de planear, leer todo lo que ya está sobre la mesa.* El documento que define cómo te
califican no es contexto opcional: es el requisito de más alta prioridad del proyecto.

**Decisiones del tech lead registradas:**
1. Teams es el canal primario y se ataca primero (**ADR-009**).
2. El frontend es **React**, no Angular — corrección respecto a la propuesta original.
3. La verificación de E2/E3/E4 se posterga; prioridad al avance técnico.
4. El RAG sobre documentos sale del alcance calificado.

**Incidencia menor:** `.gitignore` aparece con 218 líneas modificadas y contenido idéntico —
diferencia de fin de línea CRLF/LF de Windows. Se corrige con un `.gitattributes` que fije
`* text=auto eol=lf`. Diffs ruidosos ocultan diffs reales.

---

## Sesión del 8-sep-2026 (tarde) — El tenant deja de ser un riesgo y pasa a ser un procedimiento

**Decisión del tech lead:** no se paga el tenant. Se reconstruye cuando haga falta. Por tanto,
**cada paso de configuración se registra ahora**, mientras la información está fresca, para poder
reconstruir y para alimentar la guía de clientes.

### Corrección del mentor a la petición: son DOS documentos, no uno

La petición fue *"armemos un manual, me sirve cuando cree la otra cuenta y cuando cree el manual
para que otras empresas usen el servicio."* **Son dos documentos con públicos casi disjuntos**, y
fundirlos habría sido un error de fondo:

| | `RUNBOOK-TENANT.md` | `GUIA-INSTALACION-TI.md` |
|---|---|---|
| Lector | El proveedor (Iker) | El admin de TI del cliente |
| ¿Crea tenant? | Sí | **No.** Ya tiene el suyo |
| ¿Registra app en Entra? | Sí | **No.** La app ya existe y es multiinquilino |
| ¿Genera secretos? | Sí | **Nunca** |
| Pasos | 10 | 3 |

> **Por qué importa arquitectónicamente:** en el modelo ISV (ADR-003) el cliente **no registra
> nada**. Si la guía de cliente le pidiera crear un registro de aplicación, estaría confesando que
> el proyecto no tiene un producto sino un tutorial. **La brevedad de la guía de cliente es la
> demostración de que el modelo ISV funciona.**

### `RUNBOOK-TENANT.md` — reconstrucción en 10 pasos

Contiene: las tres vías de obtención de tenant con su resultado real; las **5 decisiones
irreversibles**; la ruta crítica; qué NO transfiere entre tenants; los 10 pasos con evidencia y
trampas verificadas; qué es automatizable; y las fechas que vencen.

**Hallazgos de método que quedaron escritos:**

1. **La ruta crítica es P2** (habilitar carga de apps personalizadas): hasta 24 h de propagación.
   Va primero, antes que nada, y lo demás se hace mientras espera. *La primera vez costó seis días
   de retraso por hacerlo tarde.* **Regla general: identifica qué tiene latencia externa y
   dispáralo antes que todo lo demás.**
2. **Los tres campos `developer` del manifiesto siguen con la identidad del scaffold** (`My App,
   Inc.`, `example.com`). Teams exige URLs válidas de privacidad y términos para publicar, y es lo
   primero que mira un admin para juzgar si una app es legítima o phishing. **Nuevo riesgo R16.**
   Es el mismo patrón que el `requirements.txt` del 2-sep: *confiar en un scaffold es heredar las
   decisiones de otro sin revisarlas* — solo que aquí lo heredado es la identidad del producto.
3. **El script de siembra necesitará permisos de escritura que Brújula no debe tener.** Decisión
   registrada: **registro de app separado y de un solo inquilino** (`brujula-seed`), jamás
   distribuido. Añadir `ReadWrite` a Brújula "solo para sembrar" ahorraría diez minutos y
   destruiría el argumento más fuerte del producto ante un admin de TI. **Nuevo riesgo R17.**
4. **Si solo se automatiza una cosa, que sea P9 (siembra de datos).** Es el paso más largo, el
   único que se repite con frecuencia —no solo al cambiar de tenant, sino cada vez que se quiere un
   estado limpio— y el único cuyo resultado usan los tests. Automatizar P1–P8 sería optimizar lo
   que no duele.
5. **P10.3 convierte el runbook en un test de acoplamiento.** Reconstruir el tenant y arrancar el
   sistema cambiando **solo el `.env`** es la prueba empírica del requisito de OT-01. Si no
   arranca, se acaba de localizar un identificador escrito a fuego en el código.

> **REGLA ADOPTADA:** *un entorno que solo una persona sabe reconstruir es un punto único de fallo
> con forma de infraestructura.* El runbook no es documentación burocrática: es lo que convierte un
> riesgo (R11) en una tarea con duración conocida.

> **REGLA ADOPTADA:** *un runbook se corrige el mismo día en que se ejecuta, no después.* Un
> runbook desactualizado es peor que ninguno, porque alguien lo va a seguir igual.

### `GUIA-INSTALACION-TI.md` — borrador honesto

Escrita **para el que decide, no para el que usa**. Aplica la regla adoptada en OT-01: *no se
diseña para el usuario final, se diseña para el administrador de TI que decide si la app entra.*

Decisiones de redacción registradas:

- **El procedimiento de revocación va en la portada, no en un anexo.** Un administrador confía en
  lo que puede desinstalar; esconder cómo se quita da la señal contraria.
- **La falta de *Verified Publisher* se declara en el documento** (§7) en vez de dejar que el admin
  la descubra en la pantalla de aprobación.
- **Se le pide explícitamente al admin que compare la lista de permisos** y que no apruebe si ve
  algo distinto de los cinco de lectura. Es la defensa del cliente contra un enlace suplantado, y
  a la vez la demostración de que no hay nada escondido.
- **La sección 6 (tratamiento de datos) queda marcada 🔴 y en blanco.** Depende de OT-03B
  (proveedor de LLM) y OT-04 (persistencia). **Es la primera sección que lee un administrador con
  criterio: la guía no se envía a nadie hasta completarla.** Dejarla a medias sería peor que no
  tener guía.

### Estado del runbook

Los pasos **P1–P5 y P10 están completos y verificados** (salieron de configuraciones ya ejecutadas).
**P6, P7 y P8** (registro de bot, túnel, paquete de app) quedan marcados ⏳ y se completan al
ejecutar OT-03A Fase 4. Hasta entonces el runbook está incompleto en su tercio final y **no permite
reconstruir de punta a punta.**

---

## Sesión del 8-sep-2026 — Cierre de OT-02B (auditada) y redacción de OT-03A

### Auditoría de la entrega: se ejecutó, no se leyó

El código se subió desde el repo a un entorno limpio y se corrió la suite completa, los linters,
y **sabotajes deliberados** de la *fitness function* para comprobar que sabe fallar.

| Criterio | Resultado |
|---|---|
| `pytest` | ✅ **28 tests verdes** (2 más de los pedidos) |
| `mypy --strict` | ✅ Success, 22 archivos |
| `ruff check` | ✅ All checks passed |
| `GET /health` · `GET /api/agenda` | ✅ 4 pendientes ordenados, el de `MENSAJE` al 72% |
| App de Entra ID | ✅ **Multiple organizations**; 5 permisos delegados concedidos; **cero `ReadWrite`** |
| `.env` ignorado / `.env.example` versionado | ✅ mismas claves, sin secretos |
| Flujo de PR | ✅ **PR #1 mergeada** desde `feat/esqueleto-hexagonal` |
| Sabotaje: `import fastapi` en el dominio | ✅ **FALLA** con el mensaje correcto |
| Sabotaje: servicio importa adaptador | ✅ **FALLA** con el mensaje correcto |

**La fitness function del ADR-004 funciona. No es decorativa.**

### Lo que hizo bien el tech lead (registrado, porque también es evidencia)

1. **Tradujo las carpetas al español y actualizó el test de arquitectura en consecuencia.** Si lo
   hubiera pegado sin entenderlo, los bucles habrían iterado sobre listas vacías y los seis tests
   habrían pasado en verde sin revisar nada. La guarda `test_hay_archivos_que_revisar` existía
   para atrapar justo ese caso. **Leyó el código, no lo copió.**
2. Añadió un invariante propio: `test_rechaza_contexto_vacio_cuando_se_proporciona`.
3. Añadió `extend-exclude = ["spikes"]` a ruff por iniciativa propia. El código desechable no se
   lintea.

### 🔴 Hallazgo crítico — `AZURE_TENANT_ID` mal copiado

`.env` contiene **35 caracteres**; un GUID tiene 36. Falta el primer carácter: el portal dice
`337859e0-…`, el `.env` tiene `37859e0-…`.

**No rompe nada hoy.** Los 28 tests pasan, la app arranca, `/api/agenda` responde. Nada lee todavía
esa variable. Habría explotado en **OT-05**, contra Microsoft, con un `AADSTS900023` o un 401
opaco, tres semanas después de la causa.

> **REGLA ADOPTADA:** *un dato de configuración mal copiado es un bug silencioso de latencia
> larga.* El código no lo valida porque "es solo configuración", y la distancia entre causa
> (un `Ctrl+V` incompleto) y síntoma (un 401 en tres semanas) lo hace carísimo de diagnosticar.
>
> **La corrección no es "tener más cuidado" — eso no es una estrategia de ingeniería.** Es la
> misma que ya se aplicó en `Pendiente.__post_init__`: **si un valor inválido no puede existir, no
> hay que acordarse de comprobarlo después.** OT-03A añade validación de formato GUID a
> `Configuracion`. El bug pasa a ser imposible.

### Otros hallazgos abiertos

| # | Hallazgo | Estado |
|---|---|---|
| 2 | `ruff format --check` falla: 11 archivos | Se cierra en F0 de OT-03A |
| 3 | **OT-02A sigue abierta:** sin captura del bot en Teams | Se cierra en F4 de OT-03A |
| 4 | ~~`spikes/teams-hello/` sigue rastreado~~ | **Retirado.** No es un hallazgo: es una decisión del tech lead ya registrada (R12, conservarlo como material de demostración). El mentor la había clasificado como omisión sin leer antes el registro del propio tech lead |
| 5 | ~~Se volvió a trabajar sobre `main`~~ | **Retirado.** El PR #1 estaba mergeado; estar en `main` después de un merge es correcto. La única modificación sin commitear era la edición en curso de la bitácora |
| 6 | `README.md` tiene una línea | §9: *"la cara del portafolio"*. Se cierra en F5 |

### Decisión del tech lead: prioridad al avance demostrable

Petición registrada: *"me gustaría ver todo más funcional, ver conectado el chat realmente, ir
mostrando entregas de valor para ver el feedback"*.

**Se invierte el orden del tablero.** Siguiendo el precedente 02A/02B, la OT-03 se parte:

| | Contenido |
|---|---|
| **OT-03A** | El bot de Teams responde desde el núcleo hexagonal real |
| **OT-03B** | Puerto `LLMProvider` + `FakeLLMProvider` + adaptador Gemini |

**Justificación:** (1) es la entrega de valor mostrable; (2) convierte el ADR-004 de promesa en
prueba —dos canales llamando al mismo `ServicioAgenda`—; (3) un LLM sin canal es invisible;
(4) el checkpoint es el 16-sep y el criterio de "hecho" de F1 exige el bot vivo en Teams;
(5) cierra OT-02A con evidencia mejor: el código permanente, no el spike.

### 🎯 Hallazgo técnico — se resuelve la pregunta abierta del 2-sep: UN proceso, no dos

La bitácora dejó abierto (Hallazgo 4 del 2-sep): *"el SDK oculta el servidor HTTP — dato relevante
para F2, cuando haya que decidir si el bot y la API viven en el mismo proceso o en dos."*

**Resuelto leyendo el código del SDK y después ejecutándolo.**
`microsoft_teams/apps/http/fastapi_adapter.py` expone
`FastAPIAdapter(app: Optional[FastAPI] = None)`: **acepta la instancia de FastAPI del proyecto.**
Y `AppOptions` acepta `http_server_adapter`. Verificado en ejecución:

```
Rutas ANTES de montar el bot:    GET /health · GET /api/agenda
Rutas DESPUES de montar el bot:  GET /health · GET /api/agenda · POST /api/messages
Es la MISMA instancia de FastAPI? True
```

**Veredicto: un proceso, un desplegable, un servidor.** Coherente con ADR-004. La alternativa —bot
en 3978 llamando por HTTP al núcleo en 8000— habría añadido un salto de red, un segundo desplegable
y una fuente de fallos a cambio de nada.

> **Munición de sustentación.** A *"¿por qué FastAPI?"* había ya una respuesta desde el 2-sep (el
> SDK está construido sobre él). Ahora hay una segunda, más fuerte: **el SDK acepta la instancia de
> FastAPI del proyecto, así que bot y API comparten servidor, modelo de datos y ciclo de vida.**

### Decisión de arquitectura: adaptadores primarios vs secundarios

OT-03A introduce la distinción y la hace **verificable**:

- **Primario (*driving*)**: el mundo exterior entra por él. `app/api/` (HTTP), `app/bot/` (Teams).
  Pueden llamar a los servicios.
- **Secundario (*driven*)**: el sistema lo llama a él. `app/adaptadores/`. **No** pueden llamar a
  los servicios.

Confundirlos invierte la dirección de las flechas y crea dependencias circulares entre capas.

**Reestructuración asociada:** `app/api/main.py` → `app/api/rutas.py` (un `APIRouter`), y nace
`app/main.py` como **composition root**, el único módulo que conoce los dos canales. Así ningún
canal importa al otro, y esa independencia —que es literalmente lo que afirma el ADR-009— pasa a
estar cubierta por un test.

### Tres reglas nuevas en la fitness function, todas verificadas por sabotaje

| Regla | Afirmación que deja de ser una promesa |
|---|---|
| Adaptadores secundarios no llaman a servicios ni a canales | Las flechas apuntan hacia adentro también en el lado derecho del hexágono |
| Ningún canal importa a otro canal | **ADR-009: el núcleo es agnóstico del canal.** En F4, la prueba de que la web no hizo trampa |
| `tarjeta_agenda.py` solo conoce el dominio | La presentación es una función pura y por eso se testea sin Teams |

### Hallazgo de ecosistema — el SDK no publica tipos

`microsoft-teams-apps 2.0.16` **no trae marcador `py.typed` ni stubs `.pyi`** (verificado). Bajo
`mypy --strict` produce 7 errores.

> **REGLA ADOPTADA:** *cuando una dependencia externa obliga a relajar una regla de calidad, la
> relajación se acota al módulo que la toca, nunca al proyecto.* La excepción cabe en
> `app.bot.bot_teams`. Y el corolario es medible: **el tamaño de esa excepción es una métrica de
> si la Capa de Bot Delgada (ADR-001) sigue siendo delgada.** El día que hubiera que extenderla a
> `app/servicios/`, la capa habría dejado de serlo.

Es la materialización exacta del riesgo residual anotado al cerrar R4: *el SDK es GA, pero su
tooling de tipos no lo es.*

### Correcciones del mentor en esta sesión

| # | Defecto | Qué lo detectó | Corrección |
|---|---|---|---|
| 1 | Las dos líneas útiles del bot vivían **dentro** del handler | El intento de escribir un test sin Teams: no había nada testeable | Se extrajo `construir_respuesta_agenda()`. **Regla: el handler se queda con la entrada/salida y nada más** |
| 2 | `field_validator` tipaba `info` como `object` | `mypy --strict` | `ValidationInfo`. Un `object` para no pensar el tipo es tipado de mentira |
| 3 | Se asumió que el SDK traía tipos | `mypy` + verificación de `py.typed` | Excepción acotada, con el razonamiento escrito en `pyproject.toml` |

> El defecto 1 es el más instructivo: **no lo detectó una herramienta, lo detectó el intento de
> escribir un test.** Cuando algo es difícil de testear, casi nunca es culpa del test: es el diseño
> avisando.

### Verificación previa de la OT-03A

Todo el código de OT-03A se escribió **sobre el código real del repo** y se ejecutó antes de
entregarlo: **57 tests verdes**, `mypy --strict` limpio (29 archivos), `ruff check` y
`ruff format --check` limpios, los tres endpoints en una sola instancia de FastAPI, y los tres
sabotajes nuevos produciendo fallo. Los bloques de código del documento se **inyectaron desde los
archivos verificados**, no se transcribieron.

No verificable desde el entorno del mentor y marcado como tal en la orden: comandos de
`devtunnel`, sideload y capturas.

---

## Sesión del 7-sep-2026 — Redacción y verificación de la OT-02B

**Naturaleza de la sesión:** planeación y diseño, sin escribir código en el repo.
**Entregable:** `docs/OT-02B.md` — orden de trabajo ejecutable, en 6 fases con compuertas.
**Decisión de proceso del tech lead:** modo **Guíame**. Todo el código lo escribe Iker; el mentor
entrega contrato, explicación y revisión. La ejecución se hace en una sesión aparte.

### Auditoría del estado real del repo (verificada, no reportada de memoria)

| Verificación | Resultado |
|---|---|
| `git log --oneline` | 3 commits, **todos directo sobre `main`** |
| `git status` | `.gitignore` modificado: 218 inserciones / 218 borrados, **contenido idéntico** (ruido CRLF, sin resolver desde el 2-sep) |
| `git branch` | Solo `main`. La convención del §9 del plan (`feat/` + PR) **no se estaba cumpliendo** |
| `.gitattributes` | **No existía** (pendiente #4, abierto desde el 2-sep) |
| `app/`, `tests/`, `pyproject.toml` | **No existían.** OT-02B en cero |
| `spikes/teams-hello/` | Vivo, con `.venv/` y `.env` adentro (pendiente #3, abierto) |

**Hallazgo de proceso:** cuatro de los seis pendientes registrados el 2-sep seguían sin ejecutar
cinco días después. Un pendiente escrito en la bitácora sin fecha ni compuerta es una intención,
no una tarea. **Corrección adoptada:** la OT-02B organiza los pendientes en fases con compuerta
de salida verificable, no en una lista.

### Decisiones tomadas

1. **Desacoplar OT-02A de OT-02B.** El único pendiente de 02A es el sideload, que dependía de la
   propagación de una directiva externa. Esperar a Teams para escribir código permanente violaba
   la regla ya adoptada en OT-01: *nunca poner una dependencia humana o externa dentro del ciclo
   de iteración.* El sideload entra como **Fase 1 de la OT-02B**, con límite de 15 minutos.
2. **La higiene de Git va antes del primer commit de `app/`.** `.gitattributes` y la
   renormalización CRLF cuestan tres minutos hoy y una tarde después de crear treinta archivos.
3. **Alcance cerrado:** hoy esqueleto + tooling + tests + app de Entra ID. **La conexión con el LLM
   queda para OT-03.** Los *puertos* sí se definen — un puerto es un contrato, no una dependencia.
4. **Se añaden tres criterios de aceptación** que no estaban en la OT-02B original: endpoint
   `GET /api/agenda` funcionando end-to-end sin red, *fitness function* de arquitectura, y entrega
   por PR desde `feat/esqueleto-hexagonal`.

### Presión de calendario registrada

Hoy 7-sep. **Tenant vence el 15-sep (8 días). Checkpoint del curso el 16-sep (9 días).**
El criterio de “hecho” de F1 exige el bot vivo *dentro de Teams*, y eso depende de un tenant que
puede caducar **un día antes del checkpoint**. **La captura de evidencia hay que tomarla antes del
15, no después.** Una captura sobrevive a la muerte de un tenant; un tenant caído no se reconstruye
en 24 horas.

### Decisiones de arquitectura incorporadas a la OT-02B

| Decisión | Justificación breve |
|---|---|
| `Pendiente` valida sus invariantes en `__post_init__` | Convierte la trazabilidad obligatoria de una promesa documental en un `raise`. *Hacer irrepresentables los estados ilegales.* |
| Entidad nueva **`Agenda`** con campo `fuentes_fallidas` | La regla no negociable de OT-01 (*fallo ≠ vacío*) deja de ser una nota y pasa a ser **un campo del tipo de retorno**. Permite resultado parcial honesto en vez de todo-o-nada. |
| Puertos como `Protocol`, no como `ABC` | Tipado estructural: el adaptador no importa el puerto. La compatibilidad se verifica por forma, no por linaje. |
| Puertos **`async` desde el día 1** | En OT-05 serán llamadas HTTP a Graph en paralelo. Convertir una interfaz síncrona en asíncrona después contamina toda la cadena (*function coloring*). |
| `ahora` se inyecta como parámetro, no se lee del reloj | *Toda fuente de no-determinismo es una dependencia, y toda dependencia se inyecta.* Mismo principio que el `FakeLLMProvider`. |
| El servicio captura `FuenteNoDisponibleError` pero **re-lanza** el resto | Un `KeyError` es un bug propio y debe explotar. Atrapar todo por igual disfrazaría cada bug de “fuente caída”. |
| DTOs de API separados del dominio | No es preferencia estilística: es **consecuencia forzada** del ADR-004, que prohíbe Pydantic en `domain/`. |

### ⭐ Aporte nuevo: *fitness function* de arquitectura

`tests/test_arquitectura.py` parsea con `ast` cada archivo de `app/` y verifica automáticamente las
reglas de dependencia del ADR-004: el dominio solo importa librería estándar, los puertos solo
conocen el dominio, los servicios no conocen adaptadores ni FastAPI.

> **Por qué importa.** Una arquitectura no muere de un golpe: muere de un import puesto a las dos
> de la mañana tres semanas antes de la entrega. Nadie lo revisa, nadie se entera, y el diagrama
> sigue mintiendo. Este test lo hace imposible sin que algo se ponga rojo.
> **Ante “¿cómo sé que su arquitectura es lo que dice el diagrama?” la respuesta es correr el test
> en vivo.** Término técnico para la sustentación: *fitness function* (Neal Ford,
> *Building Evolutionary Architectures*).

### Verificación previa de la orden — se ejecutó antes de entregarla

Todo el código de la OT-02B se levantó y se ejecutó en un entorno desechable antes de escribirlo
en el repo:

| Comprobación | Resultado |
|---|---|
| `pytest` | **26 tests verdes** |
| `mypy --strict` | **Success: no issues found in 22 source files** |
| `ruff check .` | **All checks passed** |
| `GET /api/agenda` | 4 pendientes ordenados, el de `MENSAJE` marcado `es_inferido: true`, `confianza 0.72` |
| **Sabotaje del test de arquitectura** | `import fastapi` inyectado en `app/domain/pendiente.py` → el test **falló** con el mensaje correcto. Revertido. |

> **REGLA ADOPTADA:** *un test que nunca has visto fallar no sabes si funciona.* Toda
> *fitness function* se verifica saboteando deliberadamente lo que protege.

### Correcciones del mentor registradas (4 defectos en la primera versión de la orden)

| # | Defecto | Qué lo detectó | Corrección |
|---|---|---|---|
| 1 | `pyproject.toml` eximía a los tests de anotar el retorno | `mypy --strict` → 26 errores | Se quitó la exención. La regla de `ruff` no silenciaba a `mypy`: la configuración se contradecía a sí misma |
| 2 | `pytest.raises(Exception)` genérico | `ruff` B017 | `FrozenInstanceError` concreto. Un `raises(Exception)` pasa aunque el fallo sea por otro motivo: da falsa confianza |
| 3 | `# type: ignore[union-attr]` en el test de arquitectura | `ruff` SIM102 | Se extrajo un helper y el `ignore` desapareció solo |
| 4 | `servicio: T = Depends(...)` | `ruff` B008 | `Annotated[T, Depends(...)]`, el idioma actual de FastAPI |

> **Lección:** los cuatro defectos pasaban los 26 tests en verde. `pytest` dice si el código *hace*
> lo correcto; `mypy` y `ruff` dicen si está *construido* correctamente. Son preguntas distintas.
>
> **REGLA ADOPTADA:** *cuando un linter obliga a poner un `# type: ignore` o un `# noqa`, casi
> nunca es la herramienta la que se equivoca: está señalando un diseño mejorable.* El defecto 3
> es el caso exacto.

---

## Sesión del 8-sep-2026 — Ejecución de OT-02B: Fases 0 a 4 cerradas

**Naturaleza de la sesión:** primera sesión de ejecución de código bajo modo **Guíame**. Iker
escribió todo el código; el mentor entregó contrato, explicación y revisión línea por línea.

### Qué quedó cerrado y verificado

| Fase | Entregable | Verificación |
|---|---|---|
| F0 | `.gitattributes` (`* text=auto eol=lf`), `.gitignore` con regla `docs/OT-*.md` | Ruido CRLF de 218 líneas resuelto a 0. Documentos de trabajo (`OT-*.md`) fuera del repo por decisión del tech lead — no son estado durable |
| F2/F3 | `dominio/`, `puertos/`, `servicios/`, `adaptadores/`, `api/` completos. `Pendiente`, `Agenda`, `ServicioAgenda`, `FuenteEjemplo`, FastAPI con `/health` y `/api/agenda` | 28 tests verdes, `mypy --strict` limpio, `ruff check .` limpio. *Fitness function* de arquitectura (`tests/test_arquitectura.py`) saboteada deliberadamente y verificada roja antes de confirmarla verde |
| F4 | App multiinquilino registrada en Entra ID. `signInAudience: AzureADMultipleOrgs` verificado en Manifest. 5 permisos delegados, 0 `ReadWrite`, consentimiento de admin otorgado (verificado en *API permissions*, no solo asumido por el redirect) | Evidencia en `docs/evidencia/` |

**Decisión de nomenclatura (tech lead):** las cuatro carpetas de la arquitectura hexagonal se
nombran en español — `dominio`, `puertos`, `servicios`, `adaptadores` — en vez del inglés
`domain/ports/services/adapters` de la OT-02B original. Los archivos internos de cada capa
conservan sus nombres originales. El mentor registró una objeción (esos cuatro nombres son el
vocabulario fijo internacional del patrón Ports & Adapters, no vocabulario de negocio en el sentido
de DDD) pero la decisión del tech lead se ejecutó tal cual.

**Hallazgo nuevo en Entra ID:** el portal advierte que *"End users cannot grant consent to newly
registered multitenant apps without verified publishers"*. Pendiente para la futura Guía de
Instalación (requiere alta en el Microsoft Partner Network; no se resuelve hoy).

### Decisión: Fase 1 diferida

El tech lead decidió posponer el sideload en Teams (cierre real de OT-02A) para priorizar el
avance del esqueleto. **Riesgo actualizado:** el tenant `brujulateams.onmicrosoft.com` vence el
15-sep-2026. La evidencia de F1 debe capturarse antes de esa fecha o deja de ser capturable para
este tenant (ver R11 en Riesgos).

### Decisión: Fase 5 fraccionada entre sesiones

Commits ya realizados y pusheados a `feat/esqueleto-hexagonal` (no siguen el patrón exacto de
`F5.2` en `OT-02B.md`, que asumía carpetas en inglés y commits aún no hechos; el criterio de fondo
— log legible por unidad lógica — se cumple igual):

```
63538dd test: cobertura de dominio, servicios, API y estructura de la arquitectura hexagonal
8cb2d07 feat: construccion FastAPI, endpoint de salud y agenda, tests, backend en memoria
8f1ecda feat: dominio completo, contratos, servicios y adaptadores, config.py
e319b54 fix: reorganizar adaptadores/servicios, mover tests a raiz y agregar tooling
72d2363 feat: creacion completa estructura del proyecto
```

**8-sep, actualización:** `feat/esqueleto-hexagonal` pusheada a `origin`. Pull Request contra
`main` abierto por el tech lead el mismo día.

**Pendiente, a ejecutar por el tech lead directamente en una sesión futura:**
1. Borrar `spikes/teams-hello/` — condicionado a tener la evidencia de F1 (regla ya existente en
   `OT-02B.md`, F5.1). **Decisión adicional del tech lead:** conservarlo más allá de ese punto,
   como material de demostración para la profesora. Ver R12 en Riesgos.
2. Actualizar `spikes/README.md` con las conclusiones antes de borrar.

### Pregunta de comprensión abierta (batch de fin de OT, aún no cerrado)

Pendiente de responder por el tech lead: *¿por qué en `test_servicio_agenda.py` el pendiente sin
fecha (`vence=None`) se ordena al final y no al principio? ¿Es una decisión técnica o de producto?*

---

## OT-02A — Spike desechable: ver un bot vivo en Teams

**Objetivo:** responder **una sola pregunta** — *¿puedo hacer que un bot responda dentro de Teams
en el tenant `brujulateams`?* Nada más.

**Time-box: 6 horas.** Si a las 6 horas no hay un bot respondiendo, se detiene, se documenta dónde
se atascó y se decide. Un spike sin límite de tiempo deja de ser spike y se vuelve un pozo.

> 💡 **Spike**: experimento acotado y **desechable** cuyo producto no es código, sino
> **conocimiento**. Se mide por lo que enseña, no por lo que queda.

### Reglas no negociables
1. Vive en `spikes/teams-hello/`. **Esa carpeta se borra al terminar.**
2. **Puede estar en TypeScript o C# si el Toolkit los soporta mejor que Python.** Como se bota, el
   lenguaje da igual. Lo único que prueba es la plomería: túnel → registro del bot → sideload.
3. **Cero lógica de negocio.** Un bot *echo* que devuelva el mensaje en mayúsculas es suficiente.
4. El scaffold del Toolkit **jamás** se convierte en la base del proyecto (ADR-001, ADR-004).

### Pasos
1. **Habilitar carga de apps personalizadas** en el tenant propio: Centro de administración de Teams
   → Aplicaciones de Teams → Directivas de configuración → Global → *"Cargar aplicaciones
   personalizadas"* = **Activado**. Iker es admin global; puede hacerlo. *(La propagación puede
   tardar horas. Hacerlo primero.)*
2. Instalar en VS Code la extensión **Microsoft 365 Agents Toolkit** (antes *Teams Toolkit*) y
   Node.js LTS.
3. Crear un proyecto desde plantilla: **Bot básico / Echo Bot**. Anotar qué lenguajes ofrece la
   plantilla — **ese dato es evidencia directa sobre el riesgo R4**.
4. Iniciar sesión con `proyectotic1@brujulateams.onmicrosoft.com`.
5. Ejecutar *Provision* y luego *Debug (Preview in Teams)*. El Toolkit levanta un túnel de
   desarrollo y hace el sideload solo.
6. Escribirle al bot en Teams. Capturar pantalla.

### Qué reportar (esto es el entregable real)
- ✅/❌ ¿Respondió el bot? Captura.
- **¿Qué lenguajes ofrecía la plantilla y había Python?** → veredicto sobre R4.
- ¿Qué recursos creó el Toolkit en Azure y en Entra ID? (Azure Bot Service, app de Entra, etc.)
- ¿Qué archivos del scaffold contienen el `APP_ID`, el `BOT_ENDPOINT` y el manifiesto?
- **¿Qué URL exacta recibe el mensaje del usuario?** ← el dato más importante: ese es el único punto
  donde el adaptador de bot tocará el núcleo.
- Dónde se atascó, si se atascó.

### Verificación adicional (2 min en Graph Explorer, alto valor)

La OT-01 probó `/me/joinedTeams` (los equipos) pero **nunca los mensajes dentro de un canal**.
Esa es la frontera real de "que la IA lea todo el Teams del usuario". Ejecutar:

```
GET /me/joinedTeams
GET /teams/{team-id}/channels
GET /teams/{team-id}/channels/{channel-id}/messages
```

**Reportar:** ¿la tercera responde 200 o 403? ¿Qué permiso pide exactamente y quién lo aprueba?

**Por qué importa:** `Chat.Read` (ya confirmado ✅) cubre chats 1-a-1 y grupales.
Los mensajes de **canal** van por `ChannelMessage.Read.All` — Protected API con consentimiento de
administrador. Y es justo ahí donde vive el contenido académico: el anuncio del profesor en el canal
de la materia. **Es la fuente `MENSAJE` de la entidad `Pendiente` (ADR-005).**

Si sale 403: la vía es **RSC** (*Resource-Specific Consent*) — el dueño del equipo autoriza la app
sobre **ese** equipo, sin pasar por el admin del tenant. Encaja perfecto con el modelo ISV (ADR-003)
y con el hecho de que Iker es dueño de los equipos de su propio tenant.

**Consecuencia si no se resuelve:** Brújula agrega Planner + To Do + Calendario, pero pierde el
diferenciador frente a Copilot — detectar compromisos implícitos en la conversación.
Mejor saberlo hoy que en octubre.

### Criterio de aceptación
- [ ] Carga de apps personalizadas habilitada en el tenant
- [ ] Bot *echo* respondiendo dentro de Teams (con captura)
- [ ] Veredicto documentado sobre el soporte de Python (riesgo R4)
- [ ] Identificado el punto de entrada del mensaje (endpoint y forma del payload)
- [ ] `spikes/teams-hello/` marcado como desechable en el README

---

---

## OT-02A — RESULTADOS REGISTRADOS (2-sep-2026, sesión de tarde)

> **Estado: ejecutada al 80%. Pendiente únicamente la prueba de sideload en Teams real.**
> Duración: ~3 h de las 6 del time-box. El time-box **no se agotó**: se detuvo por una
> dependencia externa (propagación de directiva), no por bloqueo técnico.

### Resumen ejecutivo

El spike respondió su pregunta sobre el SDK, y lo hizo **mejor de lo esperado**: el riesgo R4,
clasificado como *"el más caro del plan"*, **baja de 🔴 rojo a 🟢 verde**. No solo existe SDK de
Python: está en GA y **corre sobre la misma pila que el ADR-001 ya había elegido**.

Ningún hallazgo salió de un tutorial. Todos salieron de **leer lo que las herramientas ya estaban
diciendo**: una lista de un asistente, un `requirements.txt`, un mensaje de error de `pip`, un
árbol de dependencias y un panel de logs.

---

### Línea de tiempo de la sesión

| Hora | Hecho |
|---|---|
| 15:24 | *"Cargar aplicaciones personalizadas" = **Activado*** en la directiva Global del tenant. Inicia propagación (hasta 24 h). |
| ~16:00 | Toolkit instalado. Scaffold generado en `spikes/teams-hello/`. |
| ~16:30 | Auditoría del scaffold. Hallazgos de SDK y dependencias. |
| ~16:45 | `pip install` → falla → **entrega el catálogo real de versiones**. Se corrige y se instala limpio. |
| 16:47 | **Playground conectado a `http://127.0.0.1:3978/api/messages`.** El bot responde 200. |

---

### Hallazgo 1 — La taxonomía de Microsoft en 2026 (y dónde encaja Brújula)

El asistente *Create a New Agent/App* ofrece tres familias:

| Familia | Opciones | Requiere licencia Copilot |
|---|---|---|
| Agents for Microsoft 365 Copilot | Declarative Agent · **Custom Engine Agent** · Copilot connectors | **Sí** |
| Apps for Microsoft 365 | Blank Copilot app/agent | — |
| *(sin etiqueta)* | **Teams Agents and Apps** · Office Add-in | No |

**Brújula es, en la nomenclatura oficial de Microsoft, un *custom engine agent*:** orquestación
propia y LLM propio. Microsoft le puso nombre a la categoría del proyecto.

Se implementa hoy sobre la superficie **Teams** (ADR-009) porque el tenant de prueba
—M365 Business Standard— **no tiene licencia de Copilot**.

**Vía de expansión documentada:** exponer el mismo núcleo como *custom engine agent* dentro de
Copilot es escribir **un adaptador nuevo**, no reescribir el sistema (ADR-004).

> **Munición para la pregunta 1 de sustentación** (*"¿por qué no Copilot?"*): la respuesta deja de
> ser defensiva. **Copilot no es un competidor: es una superficie más donde Brújula puede
> publicarse.** Copilot pilotea; la brújula ubica; y el mismo núcleo sirve a ambos canales.

**Observación de riesgo:** dentro de *Teams Agents and Apps*, la opción de bot simple **ya no
existe como categoría de primer nivel**: está enterrada bajo *"Other Teams Capabilities"* →
*"Simple Bot"*. Las tres opciones destacadas traen IA precargada (Teams AI Library + LLM).

> **Lectura de arquitecto:** cuando un proveedor mueve tu caso de uso a la categoría *"otros"*, te
> está diciendo dónde va a invertir su documentación y su soporte. Es una señal de riesgo a mediano
> plazo, no una molestia de interfaz.

**Descartadas conscientemente:** `Tab` (es el frontend web de F4), `Message Extension` (acción
sobre un mensaje, no conversación), `General Teams Agent` (trae orquestación propia → violaría la
regla de "cero lógica" del spike, y en F2 competiría con el orquestador del ADR-004).

---

### Hallazgo 2 — Veredicto sobre el riesgo R4: 🟢 VERDE

**Evolución del veredicto en una sola tarde. Cada paso, una fuente de evidencia distinta:**

| Momento | Fuente | Veredicto |
|---|---|---|
| Plan original | Suposición | 🔴 *"¿existe SDK de Python?"* |
| Documentación de Microsoft | `learn.microsoft.com` | 🟠 existe; hay **tres generaciones** |
| Diálogo del Toolkit | UI de la herramienta | 🟠 `Python` aparece, etiquetado **`Preview`** |
| `requirements.txt` generado | Scaffold | 🟠 pina `microsoft-teams-apps==2.0.0a8` → **alpha** |
| **Error de `pip`** | **PyPI, dato real** | 🟢 **existe `2.0.0` estable; la serie va en `2.0.16`** |

**Tres generaciones de SDK conviven:**

| Gen | Paquete | Estado |
|---|---|---|
| 1ª — Bot Framework | `botbuilder-*` | Legacy. Microsoft publica guía de migración. |
| 2ª — Agents SDK | `microsoft-agents-*` | Presentado en los docs como "el reemplazo oficial". |
| 3ª — **Teams SDK v2** | **`microsoft-teams-apps`** | **Lo que el Toolkit genera. GA en `2.0.x`.** |

**VEREDICTO FINAL R4:** *el SDK de bot de Teams para Python **es viable y está en GA**. El riesgo
residual no es de disponibilidad sino de **ecosistema**: tres SDKs en rotación en pocos años y
escasez de material de terceros para la generación vigente en Python. **Se busca en la
documentación oficial y en el código del paquete, no en Stack Overflow** — el 95% de los resultados
son de la 1ª generación y llevan a callejones sin salida.*

**El scaffold del Toolkit está desactualizado respecto a su propio SDK**: genera contra una alpha
que quedó ~70 releases atrás y que además exige `Python >=3.12,<3.14`, incompatible con el
Python 3.14.3 instalado. La versión GA `2.0.16` sí es compatible.

> **REGLA ADOPTADA:** *un mensaje de error de un gestor de paquetes no es un obstáculo: es una
> consulta al repositorio remoto que devolvió el estado real del ecosistema. **Se lee entero antes
> de intentar arreglarlo.*** Aquí, el error de `pip` fue la fuente más confiable de toda la sesión —
> más que la documentación oficial.

---

### Hallazgo 3 — 🎯 El SDK está construido sobre FastAPI. El ADR-001 queda confirmado.

Árbol de dependencias real de `microsoft-teams-apps==2.0.16`:

```
fastapi>=0.115.13      uvicorn>=0.34.3      starlette
pydantic>=2.9.0        dependency-injector>=4.48.1
httpx                  pyjwt[crypto]        pydantic-settings
```

| Antes (temor) | Ahora (dato verificado) |
|---|---|
| El SDK exigiría `aiohttp` → dos servidores, dos procesos, un puente | **El bot ES una app FastAPI** |
| ADR-001 en tensión con la herramienta | **ADR-001 confirmado por el ecosistema** |
| Pydantic era disciplina autoimpuesta (ADR-001) | **Pydantic es la base del propio SDK** |
| Inyección de dependencias era teoría de los ADR | **`dependency-injector` viene en el SDK** |

> **Material directo de sustentación.** Ante *"¿por qué FastAPI?"* la respuesta ya no es "porque es
> popular", sino: **"porque el SDK oficial de Teams para Python está construido sobre él — mi capa
> de bot y mi núcleo comparten servidor, modelo de datos y contenedor de dependencias."**
>
> La decisión del ADR-001 se tomó en agosto por razones de portafolio y *bus factor*. La evidencia
> técnica de septiembre la respalda **por un camino independiente**. Una decisión que sobrevive a
> información que no existía cuando se tomó es una decisión bien fundamentada.

---

### Hallazgo 4 — El punto de entrada, deducido y luego verificado

**Deducido** leyendo `m365agents.local.yml`:

```yaml
- uses: botFramework/create
  with:
    messagingEndpoint: ${{BOT_ENDPOINT}}/api/messages
```

**Verificado** en el log del Playground a las 16:47:

```
Connecting to your application at http://127.0.0.1:3978/api/messages ... Connected.
installationUpdate 200 · conversationUpdate 200
```

**Cadena completa del mensaje:**

```
Usuario escribe en Teams
  → Bot Framework
  → POST https://<dev-tunnel>.devtunnels.ms/api/messages
  → dev tunnel
  → localhost:3978/api/messages
  → App() de microsoft-teams-apps  (servidor FastAPI interno)
  → handler @app.on_message
```

**`POST /api/messages`, puerto 3978, es el único punto donde el adaptador de bot tocará el núcleo
de Brújula.** La ruta **no está en el código**: la crea la clase `App` por dentro. El SDK oculta el
servidor HTTP — dato relevante para F2, cuando haya que decidir si el bot y la API viven en el
mismo proceso o en dos.

> **Nota de método:** deducir y verificar son actos distintos. Se hicieron los dos, en ese orden.

---

### Hallazgo 5 — Auditoría del `requirements.txt` generado

El scaffold trae dos defectos, ambos corregidos:

| # | Defecto del scaffold | Corrección | Por qué importa |
|---|---|---|---|
| 1 | `dotenv>=0.9.9` | `python-dotenv==1.0.1` | `dotenv` es un paquete **abandonado desde 2013** cuya propia descripción dice *"THIS LIBRARY IS NO LONGER SUPPORTED, USE python-dotenv INSTEAD"*. No es typosquatting: es **abandonware**. Que un scaffold oficial de Microsoft lo instale por defecto, en 2026, es un defecto de la plantilla. |
| 2 | `microsoft-teams-apps>=2.0.0a8,<3.0.0` | `microsoft-teams-apps==2.0.16` | Un rango abierto sobre un prerelease permite que `pip` instale una versión con cambios rompientes sin aviso. El bot "que funcionaba ayer" deja de arrancar sin que nadie haya tocado el código. |

Se conservaron `requirements.txt.original` y `app.py.original` para que el diff sea auditable.

> **REGLA ADOPTADA:** *todo archivo de dependencias generado por una herramienta se **audita línea
> por línea** antes del primer `pip install`. Nombre canónico del paquete, estado de mantenimiento y
> versión fijada. Confiar en un scaffold es heredar las decisiones de otro sin haberlas revisado.*

**Instalación final:** limpia, sin conflictos, sobre **Python 3.14.3**. Único aviso:
`ExperimentalWarning` de `HtmlWidgetSecurityPolicy`, componente no utilizado por el proyecto.

**Verificación de compatibilidad de API** (`app.py` fue generado contra `2.0.0a8`, se ejecuta con
`2.0.16`): los imports de `microsoft_teams.api` y `microsoft_teams.apps` responden **`IMPORTS OK`**.
La API se mantuvo estable entre la alpha y la GA.

---

### Hallazgo 6 — Qué crea `provision` (dos buenas noticias)

**a) No consume Azure.** Para el entorno `local`, el registro del bot se hace en
`dev.botframework.com` mediante `botFramework/create`, **no** en Azure Bot Service.
El `infra/azure.bicep` existe pero solo aplica al entorno remoto.
**Los créditos de Azure for Students quedan intactos** y reservados para hospedar el backend.

**b) La app de Entra nace multi-inquilino por defecto:**

```yaml
- uses: aadApp/create
  with:
    signInAudience: AzureADMultipleOrgs   # ← multi-tenant
```

Confirma que el radio button que exige la OT-02B (**"Cuentas en cualquier directorio
organizativo"**, ADR-003, modelo ISV) es el correcto. *(La app del spike se descarta con la
carpeta; la permanente se registra a mano en OT-02B.)*

**Manifiesto generado:** `manifestVersion 1.29`, scopes `personal`, `team`, `groupChat`;
permisos `identity` y `messageTeamMembers`.

---

### Hallazgo 7 — Seguridad: protegidos por accidente, no por diseño

`provision` genera un `CLIENT_SECRET` real y lo escribe en `env/.env.local.user`.
Verificación con `git check-ignore -v`:

```
.gitignore:156:ENV/   →   spikes/teams-hello/env/.env.local.user
```

La regla que lo atrapó es **`ENV/` en mayúsculas**, del template de Python de GitHub.
Coincidió con `env/` **únicamente porque el sistema de archivos de Windows no distingue
mayúsculas de minúsculas**. En Linux —es decir, en cualquier CI— esa regla **no habría coincidido**.

Hay protección real: el `.gitignore` propio del scaffold incluye `env/.env.*.user` explícito.
Pero el hallazgo se registra igual.

> **REGLA ADOPTADA:** *estar protegido no es lo mismo que estar protegido **a propósito**. Toda
> regla de `.gitignore` sobre secretos se verifica con `git check-ignore -v` y se lee **cuál** regla
> hizo el match. Una protección que depende de la insensibilidad a mayúsculas de un sistema de
> archivos desaparece al cambiar de máquina.*

Es el mismo problema de fondo que el CRLF detectado en la auditoría del 2-sep: **el repositorio se
comporta distinto según el sistema operativo.** El `.gitattributes` pendiente deja de ser cosmético.

---

### Lo construido: demo de producto sobre el spike

Además de la prueba de plomería, se construyó una **demo honesta** para mostrar avance sin mentir.
Cuatro archivos en `spikes/teams-hello/src/`:

| Archivo | Responsabilidad | Qué demuestra |
|---|---|---|
| `dominio.py` | Entidad `Pendiente` + `FuentePendiente` (ADR-005) | **Cero imports externos.** Regla hexagonal verificable a simple vista |
| `fixtures.py` | Datos de ejemplo, marcados como falsos | Firma `-> list[Pendiente]`, **idéntica a la del futuro `TaskSource`** |
| `tarjetas.py` | `list[Pendiente]` → Adaptive Card | Único módulo que conoce Teams. La frontera hexagonal en 60 líneas |
| `app.py` | 4 handlers | Separa plomería de demo |

**Handlers:** `eco` (plomería pura, devuelve en mayúsculas) · `semana` (la tarjeta) ·
`estado` (lista honesta de lo probado y lo no probado) · `bienvenida`.

**La tarjeta muestra la tesis del proyecto en una pantalla:** cuatro pendientes de cuatro fuentes,
cada uno con `fuente`, `vence` y botón **"Ver origen"** (trazabilidad obligatoria). Los tres
provenientes de sistemas estructurados salen en **verde**, marcados *"Confirmado"*. El cuarto,
inferido de un mensaje de canal, sale en **amarillo**, con **72% de confianza** y la leyenda
*"Brújula no confirma este pendiente. Verifícalo en el origen."*

Ese contraste **es la respuesta visual a la pregunta 2 de sustentación** (*"¿y si el modelo alucina
una fecha de entrega?"*) y al *"¿por qué no Copilot?"*.

> **PRINCIPIO ADOPTADO — honestidad del avance:** *la demo declara explícitamente, en la propia
> tarjeta y en el comando `estado`, que **Graph no está conectado** y que los datos son de ejemplo.
> Demostrar el canal y el modelo de datos es un avance real; presentarlo como integración con Graph
> sería mentir. **Un proyecto que exagera su avance pierde la única moneda que tiene ante un
> evaluador.** Además: nunca poner en una demo algo que no se pueda defender bajo pregunta.*

**Nota:** todo este árbol sigue siendo **desechable**. Estos archivos son un **ensayo** del diseño;
la versión permanente se escribe desde cero en `app/` durante la OT-02B. La regla del ADR-001 no se
relaja porque el spike haya quedado bonito.

---

### Criterio de aceptación de la OT-02A

- [x] Carga de apps personalizadas habilitada en el tenant — *15:24, 2-sep*
- [ ] **Bot echo respondiendo dentro de Teams (con captura)** — *pendiente: propagación de directiva*
- [x] Veredicto documentado sobre el soporte de Python (R4) → **🟢 GA, viable**
- [x] Identificado el punto de entrada → **`POST /api/messages`, puerto 3978** (deducido y verificado)
- [x] `spikes/` marcado como desechable — `spikes/README.md`

**4 de 5.** El único pendiente depende de una espera externa, no de trabajo técnico.

---

### Correcciones del mentor registradas en esta sesión

Se registran con el mismo rigor que los errores del tech lead. **Dos veces en una tarde el mentor
predijo desde documentación y la ejecución lo desmintió.**

| # | Predicción | Realidad | Fuente que corrigió |
|---|---|---|---|
| 1 | *"El SDK usa **aiohttp**; hay tensión con el ADR-001"* | Usa **FastAPI + uvicorn**. Cero tensión. | Árbol de dependencias de `pip install` |
| 2 | *"`dotenv` huele a **typosquatting**"* | Es **abandonware** legítimo de 2013. Diagnóstico equivocado, problema real distinto. | Ficha del paquete en PyPI |

En el caso 1, el error de origen fue leer la documentación del **Agents SDK** (2ª generación) y
asumir que aplicaba al SDK que el Toolkit realmente genera (3ª generación).

> **Confirmación de la regla del 23-ago:** *"la política de una plataforma externa no se deduce de
> la documentación, se verifica ejecutándola."* Esta sesión la extiende: **aplica también al
> ecosistema de dependencias, y aplica también al mentor.** La documentación describe lo que es
> posible; solo la ejecución dice qué es cierto aquí y ahora.

---

### Pregunta de comprensión de la sesión — CERRADA

**Pregunta:** *el SDK parecía exigir un servidor distinto al del ADR-001. ¿Por qué cambiar el
ADR-001 a "lo que traiga el SDK" sería un error de arquitectura, y qué mecanismo del plan libera de
tomar esa decisión hoy?*

**Respuesta registrada:** decidir la arquitectura del núcleo a partir de lo que traiga una
herramienta externa **invierte la relación**: el proyecto pasa a servir a la herramienta.
El mecanismo que protege es la **Capa de Bot Delgada** (ADR-001): el adaptador de bot no contiene
lógica de negocio, así que un SDK hostil cuesta **un módulo**, no el proyecto.

En este caso la tensión desapareció al medirla. **Pero el valor del ADR no dependía del resultado:**
un ADR bien escrito protege igual cuando se acierta que cuando se falla. Esa es la prueba de que
estaba bien escrito.

---

### Pendientes inmediatos para la próxima sesión

1. 🔴 **Cerrar OT-02A:** `F5 → Debug in Teams (Chrome)` → provision → sideload → escribirle al bot →
   **captura**. Requiere que la directiva haya propagado (guardada 15:24 del 2-sep).
2. **Verificación de Graph pendiente** (2 min en Graph Explorer, alto valor):
   `GET /teams/{id}/channels/{id}/messages` → ¿200 o 403? Es la frontera de la fuente `MENSAJE`.
   Si da 403, la vía es **RSC**.
3. **Borrar `spikes/teams-hello/`** una vez capturada la evidencia. Mover capturas a `docs/adr/`.
4. Crear `.gitattributes` con `* text=auto eol=lf`.
5. Arrancar **OT-02B**: estructura hexagonal en `app/`, `mypy` + `ruff` desde el primer commit,
   registro de app en Entra ID multi-inquilino con los 5 permisos delegados.
6. ⚠️ **15-sep:** decidir pago del tenant (16,80 USD/mes) o migración. **Fecha crítica.**


## OT-02B — Esqueleto hexagonal + app de Entra ID

**Se ejecuta después de OT-02A y con lo aprendido en ella.** Esto **sí** es código permanente.

### Parte 1 — Estructura del proyecto
Crear el árbol del ADR-004 con archivos mínimos:

```
brujula-teams/
├── app/
│   ├── domain/pendiente.py        # entidad + enum FuentePendiente
│   ├── ports/                     # llm_provider.py, task_source.py
│   ├── services/                  # (vacío por ahora)
│   ├── adapters/                  # (vacío por ahora)
│   └── api/main.py                # FastAPI + GET /health
├── tests/
├── spikes/
├── .env.example                   # sin un solo valor real
├── requirements.txt
└── pyproject.toml                 # config de mypy y ruff
```

**Disciplina obligatoria (compensa la venida de .NET, ADR-001):** tipado estricto, `mypy` y `ruff`
configurados **desde el primer commit**. Añadirlos después es refactorizar; ponerlos al inicio es
gratis.

**Regla de dependencias, verificable:** `app/domain/` **no puede importar nada** fuera de la
librería estándar. Ni FastAPI, ni Mongo, ni el SDK de Graph. Si un import se cuela ahí, la
arquitectura hexagonal ya se rompió.

### Parte 2 — Registro de app en Entra ID (permanente, no la del Toolkit)
- Portal de Entra → Registros de aplicaciones → Nuevo registro.
- **Tipos de cuenta: "Cuentas en cualquier directorio organizativo (multiinquilino)"**
  ⚠️ Decisión difícil de revertir. Elegir "solo mi organización" ata el `CLIENT_ID` a
  `brujulateams` para siempre y ninguna empresa cliente podría instalar Brújula (ADR-003, modelo ISV).
- Permisos delegados, solo lectura: `User.Read`, `Calendars.Read`, `Tasks.Read`,
  `Team.ReadBasic.All`, `Chat.Read`. **Ni un `ReadWrite`.**
- Generar secreto y guardarlo **solo** en `.env` local. `.env.example` lleva los nombres, nunca los valores.

### Criterio de aceptación
- [ ] `GET /health` responde 200 en local
- [ ] `mypy` y `ruff` corren limpios
- [ ] `Pendiente` definido en `domain/` sin imports externos
- [ ] App multiinquilino registrada, con los 5 permisos delegados
- [ ] `.env` en `.gitignore`; `.env.example` versionado y sin secretos
- [ ] `.gitattributes` con `* text=auto eol=lf`

---

## OT-01 — Reconocimiento de plataforma

**Objetivo:** desactivar los riesgos de plataforma **antes** de escribir una sola línea de código, y tener el primer contacto real con Microsoft Graph.

**Regla:** en esta OT no se escribe código. Se investiga y se reporta.

### Tarea 1.1 — ¿La UPB permite apps personalizadas?
Abrir Teams con la cuenta UPB → **Aplicaciones** → buscar "Administrar tus aplicaciones" o "Cargar una aplicación personalizada".
**Reportar:** ¿aparece la opción, sí o no?
*(Informativo. Según ADR-003 no bloquea nada, pero define si habrá prueba de campo real al final.)*

### Tarea 1.2 — Conseguir un tenant propio
Intentar en este orden y reportar hasta dónde se llegó:

1. **Microsoft 365 Developer Program** — sandbox E5 gratuito. La elegibilidad se restringió: hoy suele exigir suscripción Visual Studio Professional/Enterprise *standard*. Verificar si la UPB da acceso a Visual Studio a sus estudiantes (programas de educación de Microsoft).
2. **Prueba gratuita de Microsoft 365 Business Standard** — 30 días, tenant real con Teams y Planner. Sirve para arrancar; hay que decidir después si se paga un usuario (~USD 12/mes) durante el semestre.
3. Si ambas fallan: reportar y se replantea.

**Reportar:** qué opción quedó viable, dominio del tenant y si tiene licencia con Teams y Planner.

### Tarea 1.3 — Primer contacto con Microsoft Graph *(la tarea que más enseña)*
Entrar a **Graph Explorer** (`developer.microsoft.com/graph/graph-explorer`), iniciar sesión y ejecutar:

```
GET https://graph.microsoft.com/v1.0/me
GET https://graph.microsoft.com/v1.0/me/events
GET https://graph.microsoft.com/v1.0/me/todo/lists
GET https://graph.microsoft.com/v1.0/me/planner/tasks
GET https://graph.microsoft.com/v1.0/me/joinedTeams
GET https://graph.microsoft.com/v1.0/me/chats
```

**Reportar por cada llamada:**
- ¿200 OK, 403, 404 o vacío?
- Si pidió consentimiento, ¿qué permiso exacto pidió y quién debía aprobarlo (usuario o admin)?
- Un ejemplo del JSON devuelto (con datos sensibles tachados).

Este es el momento donde el proyecto deja de ser teoría.

### Tarea 1.4 — Confirmar acceso a un LLM
Verificar cuál está disponible: Azure OpenAI (requiere solicitud), OpenAI directo, Google Gemini, Groq u Ollama local.
**Reportar:** cuál quedó confirmado y con qué límite de crédito o de cuota.

### Tarea 1.5 — Repositorio
Crear repo en GitHub con `README.md`, `.gitignore` de Python y carpeta `docs/adr/`. Copiar allí `PLAN-MAESTRO.md`.
**Reportar:** URL del repo.

### Resultados registrados — 23-ago-2026

**Bautizo del proyecto: `Brújula`.**
Razón: el plan define que el sistema "no resuelve las tareas; orienta, contextualiza y enlaza".
Eso es exactamente una brújula: no camina por ti, te ubica y te señala el norte.
Sirve además como respuesta a la pregunta de sustentación "¿por qué no Copilot?" — Copilot pilotea, la brújula ubica.

#### Tarea 1.1 — ✅ CERRADA. La UPB NO permite sideload.

Teams (cuenta UPB) → Aplicaciones → Administrar las aplicaciones → "Carga una aplicación"
muestra **una sola** opción: *"Enviar una aplicación a su organización — Envía una aplicación a tu
administrador de TI para tu aprobación"*. **No existe** la opción de cargar un paquete propio.

**Evidencia:** captura del diálogo. Pendiente guardarla en `docs/adr/` como respaldo de ADR-003.
ADR-003 deja de ser hipótesis y pasa a estar respaldado por evidencia.

**Por qué se descarta la vía de aprobación de TI (razonamiento del cierre):**
no es un trámite, es **un trámite por cada iteración**. Durante el desarrollo el paquete se resube
decenas de veces; si cada subida entra en una cola de aprobación, el ciclo de retroalimentación
pasa de minutos a días. **Regla adoptada: nunca poner una dependencia humana externa dentro del
ciclo de iteración.** Al final, para desplegar una vez, sí; durante el desarrollo, jamás.

**Reposicionamiento:** la UPB pasa de *entorno de desarrollo* a *cliente potencial* (modelo ISV, ADR-003).

#### Tarea 1.2 — ✅ CERRADA. Tenant propio operativo.

| Vía intentada | Resultado |
|---|---|
| M365 Developer Program (sandbox E5) | ❌ *"You don't currently qualify for a Microsoft 365 Developer Program sandbox subscription."* |
| Suscripción Visual Studio (requisito de elegibilidad) | ❌ Solo **Dev Essentials** (nivel gratuito). No es Professional ni Enterprise. |
| **M365 Business Standard — prueba 30 días** | ✅ **Tenant creado** |

- **Dominio:** `brujulateams.onmicrosoft.com`
- **Organización:** Proyecto TIC1
- **Cuenta admin:** `proyectotic1@brujulateams.onmicrosoft.com`
- **Rol:** Iker es administrador global. Acceso confirmado a admin.cloud.microsoft.
- **Costo tras la prueba:** 16,80 USD/usuario/mes.
- ⚠️ **FECHA CRÍTICA — cancelar o decidir pago antes del 15 de septiembre de 2026.**

**Requisito de arquitectura derivado (no negociable):**
cambiar de tenant debe costar **solo variables de entorno** — `TENANT_ID`, `CLIENT_ID`,
`CLIENT_SECRET`, `REDIRECT_URI`. **Cero identificadores de tenant escritos en el código.**
Es la promesa de ADR-004 aplicada a la infraestructura.

**Deuda operativa identificada:** lo que NO transfiere entre tenants no es código, son datos y
registro: la app de Entra ID (nuevo CLIENT_ID y secreto, redirect URIs, consentimientos), los
usuarios de prueba, el plan de Planner con tareas, los eventos de calendario y el equipo de Teams.
Reconstruir eso a mano son horas de clics.
**Mitigación acordada:** escribir `scripts/seed_tenant.py` que siembre todo vía Graph.
Convierte la reconstrucción de un tenant en un comando, hace los tests reproducibles y es un
artefacto de valor para el portafolio.

**Riesgo anotado:** encadenar pruebas gratuitas sucesivas es frágil — Microsoft las ata al método de
pago, teléfono y dominio. **No se construye el cronograma sobre eso.** La sustentación es en
noviembre; un tenant caído ese día deja al proyecto sin demo.

**Nota de gobernanza:** quien crea el tenant queda como administrador global. Ese rol **no se
delega por conveniencia** al equipo. A Julián y Antonio se les puede delegar el seed de datos,
nunca las llaves del tenant. (Mínimo privilegio, ADR-002, aplicado puertas adentro.)

#### Tarea 1.3 — ✅ EJECUTADA en tenant propio (23-ago-2026)

**Hallazgo central:** en el primer intento, **solo `/me` respondió 200**. Las otras cinco dieron **403**.
La causa no era la cuenta ni el tenant: el token de Graph Explorer arranca con el mínimo
(`openid, profile, User.Read, email`). **Faltaban los scopes, no los privilegios.**

**Estado inicial (sin consentir permisos):**

| Endpoint | Estado | Código de error |
|---|---|---|
| `/me` | 200 OK | — |
| `/me/events` | 403 | `ErrorAccessDenied` |
| `/me/todo/lists` | 403 | `notAllowed` / `ErrorAccessDenied` |
| `/me/planner/tasks` | 403 | *"You do not have the required permissions"* |
| `/me/joinedTeams` | 403 | `Forbidden` — **listó los scopes requeridos** |
| `/me/chats` | 403 | `Forbidden` — **listó los scopes requeridos** |

**Estado final (tras consentir):** las 6 en **200 OK**. La mayoría con `"value": []` porque el tenant
está recién creado y sin datos sembrados.

**Permisos identificados y consentidos (todos de solo lectura):**

| Permiso | Habilita | Alimenta `fuente` de `Pendiente` |
|---|---|---|
| `User.Read` | Identidad del usuario | — (contexto) |
| `Calendars.Read` | Eventos propios | `CALENDARIO` |
| `Tasks.Read` | To Do **y** Planner (permiso compartido) | `TODO`, `PLANNER` |
| `Team.ReadBasic.All` | Lista de equipos del usuario | previo a `MENSAJE` |
| `Chat.Read` | Contenido de chats | `MENSAJE` |

**Ni un solo `ReadWrite`.** Brújula orienta, no escribe. Mínimo privilegio verificable (ADR-002).

**Modelo mental adoptado — `Recurso.Acción.Alcance`:**
el sufijo `.All` es la frontera entre "leo lo mío" y "leo lo de la organización", y es lo que
dispara el requisito de consentimiento de administrador. `Team.ReadBasic.All` es el único con `.All`
en la lista; se pudo consentir **porque Iker es admin global de su propio tenant**.
En el tenant de la UPB ese permiso habría sido inalcanzable. **Validación en vivo de ADR-003.**

**Observación de diseño — errores heterogéneos:** Graph no responde igual en todos los servicios.
Exchange (`/me/events`) devuelve `ErrorAccessDenied` sin detalle; Teams (`/me/joinedTeams`, `/me/chats`)
devuelve el listado exacto de scopes faltantes. El adaptador de Graph deberá normalizar formatos de
error distintos según el servicio de origen.

**⚠️ REGLA DEL ADAPTADOR (no negociable):**
**nunca traducir un error de permisos a un resultado vacío.**
`200 OK` con `[]` → devolver lista vacía. `403` → **lanzar excepción**.
Colapsar ambos casos produce el peor bug posible de este proyecto: Brújula diría
*"no tienes pendientes"* cuando la verdad es *"no pude preguntar"*. El usuario confía, no estudia y
pierde la entrega. En un sistema cuyo valor es la confianza, **el silencio por error es la falla más cara**.

#### Tarea 1.3 (bis) — Comparativa contra el tenant de la UPB ✅

Misma batería, autenticado con la cuenta `@upb.edu.co`:

| Endpoint | `brujulateams` (propio) | UPB |
|---|---|---|
| `/me` | 200 OK | 200 OK |
| `/me/joinedTeams` | 200 OK | 200 OK |
| `/me/events` | 200 OK | ❌ 403 — requiere administrador |
| `/me/todo/lists` | 200 OK | ❌ 403 — requiere administrador |
| `/me/planner/tasks` | 200 OK | ❌ 403 — requiere administrador |
| `/me/chats` | 200 OK | ❌ 403 — requiere administrador |

**HALLAZGO CRÍTICO — la UPB tiene deshabilitado el consentimiento de usuario para aplicaciones.**

`Calendars.Read`, `Tasks.Read` y `Chat.Read` son permisos sobre los **datos propios del usuario** y,
en un tenant con configuración por defecto, **cualquier usuario puede consentirlos sin pasar por TI**.
Que la UPB los bloquee no es un permiso faltante: es una **política de tenant** que impide a
cualquier estudiante autorizar cualquier aplicación de terceros sobre su propia cuenta.

**Consecuencia:** Brújula **no puede funcionar en el tenant de la UPB sin intervención de TI**,
ni siquiera para leer el calendario del propio usuario.
Cierra el círculo con la Tarea 1.1: **dos candados independientes** — no se puede instalar la app
(1.1) y tampoco se podría autorizar aunque se instalara (1.3 bis).
ADR-003 queda demostrado con datos, no argumentado.

**Corrección registrada — predicción fallida del mentor:** se predijo que fallarían los permisos
con `.All` y pasarían los personales. Ocurrió **exactamente al revés** (`joinedTeams`, que lleva
`.All`, sí pasó). La documentación describe lo que es *posible*; solo la prueba revela lo que está
*permitido en un tenant concreto*.
**Lección de arquitectura: la política de un tenant no se predice, se mide.**

#### Tarea 1.4 — ✅ CERRADA. LLM confirmado.

**Decisión: Google Gemini API (capa gratuita) como proveedor principal.**
API key generada en `aistudio.google.com`. Sin tarjeta de crédito.
Límites: ~1.500 peticiones/día en modelos Flash, contexto de 1M tokens. Suficiente con margen
para el MVP y coherente con ADR-008 (modelo rápido y barato para la lista breve).

**Descartado — Azure OpenAI:** los créditos de Azure for Students (USD 100) **no se pueden aplicar
a Azure OpenAI**; es una exclusión explícita del programa. Es exactamente el escenario que ADR-006
anticipó al no hipotecar el proyecto a un proveedor incierto. Los créditos de Azure se reservan
para hospedar el backend.

**Contingencia — Ollama local** sobre el PC con GPU de Iker. No es plan B de emergencia:
desarrollo sin conexión, sin cuota y sin costo, y **demuestra ADR-006 en el repo** al correr el
sistema con varios proveedores sin tocar el núcleo.

**Hugging Face — rol asignado:** no como proveedor de chat, sino como fuente de modelos de
*embeddings* (`sentence-transformers`) ejecutados **localmente en GPU** para F3 (RAG). Elimina el
costo recurrente más peligroso de un sistema RAG. Los vectores van a MongoDB Atlas Vector Search (ADR-007).

**Detalle técnico adoptado:** Gemini, Groq y Ollama exponen API **compatible con el SDK de OpenAI**.
El adaptador se escribe contra esa forma; cambiar de proveedor = cambiar `base_url` y `api_key`.

**Reencuadre de mentoría registrado:** el valor de portafolio no está en llamar a una API de LLM
(ocho líneas, lo hace cualquiera), sino en tres cosas:
1. Proveedor intercambiable tras un puerto `LLMProvider` (ADR-006).
2. `FakeLLMProvider` determinista → tests sin red, sin costo, sin aleatoriedad. Demuestra que se
   entiende un LLM como dependencia externa no determinista.
3. Capacidad de **medir** la calidad de las respuestas (golden dataset). Es la pregunta 3 de
   sustentación, "la que tumba proyectos de IA".

#### Decisión de arquitectura anticipada para OT-02 (multi-tenant)

Al registrar la app en Entra ID hay que elegir **"Cuentas en cualquier directorio organizativo"
(multiinquilino)**. Elegir "solo mi organización" ata el `CLIENT_ID` a `brujulateams` para siempre
y ninguna otra empresa podría instalar Brújula. **Es un radio button difícil de revertir.**

El mecanismo de adopción por una organización cliente es el **admin consent**: el administrador de
TI abre una URL, revisa la lista exacta de permisos y aprueba una vez para todo su tenant.
Esa URL + esa lista **son** la *Guía de Instalación para el Administrador de TI* (entregable ADR-003).

**Corolario:** que la lista de permisos no tenga ni un solo `ReadWrite` no es purismo — es lo que
hace la app aprobable. Un admin que ve "escritura en chats" en la pantalla de consentimiento no aprueba.

#### Tarea 1.5 — ✅ CERRADA. Repositorio creado.

- **Repo:** `brujula-teams`, público, con `README.md` y `.gitignore` de Python desde el commit uno.
- `PLAN-COMPLETO.md` y `BITACORA.md` viven dentro del repo, en `docs/`.
- Se descartó `brujula` a secas: `brujula-teams` deja claro el dominio del proyecto sin abrir el repo.

**Beneficio adquirido:** `git log` sobre `docs/BITACORA.md` es el historial fechado de todas las
decisiones del proyecto. Evidencia de proceso, no solo de resultado.

**Incidencia corregida:** quedaron temporalmente **dos copias** de `BITACORA.md` (raíz del disco y
repo). Se eliminó la de la raíz. **Dos fuentes de verdad son cero fuentes de verdad.**

#### Protocolo de trabajo con IA adoptado (23-ago-2026)

**Principio: los chats son memoria de trabajo; los archivos son el estado.**
Un chat es un trabajador desechable: lee el estado desde disco, ejecuta una OT, escribe el
resultado en disco y muere. El conocimiento del proyecto **nunca** vive en un chat.

**Regla operativa:** *nada existe hasta que está escrito en `BITACORA.md`.*

1. Un chat por OT. Se cierra al cerrar la OT.
2. No mantener un "chat principal" largo: se degrada y arrastra confusiones viejas.
   Un chat corto que lee archivos frescos siempre está mejor informado.
3. Ritual de cierre obligatorio: *"actualiza la bitácora con lo de hoy y dime cuál es la siguiente OT"*.
4. Mantener la carpeta del proyecto conectada en cada chat nuevo.

**Paralelo con el propio proyecto:** es el mismo problema que resuelve Brújula. Un LLM no tiene
memoria entre sesiones; se le da contexto recuperándolo de una fuente externa confiable.
Aquí esa fuente es la bitácora; en el producto serán Graph y el vector store.
**Se está usando la arquitectura que se está construyendo.**

### Criterio de aceptación de la OT-01
- [x] Se sabe si la UPB permite sideload → **NO permite**
- [x] Existe un tenant propio con Teams y Planner → **`brujulateams.onmicrosoft.com`**
- [x] Las 6 llamadas de Graph están ejecutadas y reportadas → **en ambos tenants, con comparativa**
- [x] Hay un LLM confirmado y accesible → **Gemini API (free tier)**, contingencia Ollama local
- [x] El repo existe y es público → `brujula-teams`

---

## Registro de aprendizaje

> Cada OT cerrada exige responder preguntas de comprensión. No basta con que funcione:
> hay que entender por qué. Aquí se registran las respuestas y las brechas detectadas.

### 23-ago-2026 — Cierre de OT-01: 1/3

Mejora respecto a la verificación previa (0/3): las tres respuestas se movieron al plano de
**gobernanza y guía de instalación**, que era justo el patrón a corregir. Persisten dos huecos de fondo.

| # | Tema | Respuesta de Iker | Corrección |
|---|---|---|---|
| 1 | Por qué la UPB bloquea el consentimiento de usuario | ✅ Acertó la consecuencia (la guía debe listar permisos). ❌ No supo la causa: *"depende del negocio"*. | El ataque se llama **illicit consent grant / consent phishing**: una app maliciosa obtiene un token legítimo por consentimiento del usuario. **Ese token sobrevive al cambio de contraseña y al MFA**, porque no hubo hackeo — hubo aprobación. Por eso las organizaciones lo apagan en bloque. |
| 2 | Por qué el `FakeLLMProvider` debe ser determinista | ❌ Confundió `FakeLLMProvider` con **Ollama**. | Ollama **es un LLM real**: lento, con GPU y **no determinista**. El Fake son ~20 líneas que devuelven una cadena fija; no hay IA adentro. Determinista porque un test afirma *"esta entrada → exactamente esta salida"*. Con salida variable los tests **fallan al azar**, y el rojo intermitente enseña a ignorar el rojo: el día que algo se rompe de verdad, nadie se entera. Además: milisegundos en vez de segundos, sin cuota, y ejecutable en CI sin GPU ni API key. |
| 3 | Regla general tras la predicción fallida | ❌ Repitió el caso (*"depende de la organización"*) sin extraer la regla. | **La política de una plataforma externa no se deduce de la documentación, se verifica ejecutándola.** La doc dice qué es *posible*; solo la prueba dice qué está *permitido aquí*. Corolario: toda dependencia externa se prueba en un experimento chico y desechable **antes** de escribir código que dependa de ella. Es la razón de ser de toda la Fase 0. |

**Distinción clave que faltaba (pregunta 2):** en los tests unitarios **no se prueba el modelo, se
prueba el código propio** — orquestador, adaptadores, construcción de `Pendiente`. El LLM es una
dependencia externa que hay que anular para poder ver la lógica propia.
Medir la **calidad del modelo** es un problema distinto, con herramienta distinta: el **golden
dataset**, que corre aparte y con poca frecuencia. **Confundir ambos tipos de prueba es el error
clásico de los proyectos de IA.**

**Regla adoptada (pregunta 1):** *no se diseña para el usuario final, se diseña para el
administrador de TI que decide si la app entra.* Ese es el verdadero portero.

**Requisitos derivados para la Guía de Instalación:**
- Cada permiso justificado en una línea: qué dato lee y para qué.
- Énfasis en **cero `ReadWrite`** — es el argumento más fuerte ante un admin.
- Almacenamiento y ciclo de vida de los tokens (ADR-002).
- URL de admin consent **y procedimiento de revocación** (un admin confía en lo que puede desinstalar).
- **Verified Publisher** en Entra ID: es lo que distingue la app de una de phishing a ojos del admin.

**Riesgos reclasificados de "asumido" a "por medir" (pregunta 3):**
| Dependencia | Qué se está asumiendo | Cuándo medirlo |
|---|---|---|
| SDK de bot de Teams para Python (R4) | Que funciona | **Hola-mundo desechable en F1, no en F4.** Es el riesgo más caro del plan. |
| MongoDB Atlas Vector Search (tier gratuito) | Que alcanza | Antes de F3 |
| Cuota gratuita de Gemini | Que aguanta la demo real | Antes de la sustentación |
| Créditos de Azure for Students | Qué más excluyen además de Azure OpenAI | Antes de decidir hosting |

**Patrón raíz — actualización:** el reflejo de razonar en lo técnico ante problemas de gobernanza
**mejoró**. El patrón nuevo a vigilar es distinto: **quedarse en el caso particular sin extraer la
regla general.** Un arquitecto convierte cada incidente en una regla reutilizable.

### 15-ago-2026 — Verificación inicial (previa a OT-01): 0/3

Brechas detectadas. **Repasar antes de la sustentación.**

| # | Tema | Error cometido | Corrección |
|---|---|---|---|
| 1 | Permisos de Graph | Razonó en términos de *rendimiento* ("las peticiones duran mucho") ante un problema de **gobernanza** | El bloqueo es: Protected API + consentimiento de admin + mínimo privilegio. En integraciones empresariales frena el permiso, no la técnica. |
| 2 | Campo `confianza` | No identificó su función | Distingue **hecho** (Planner, `1.0`) de **inferencia del LLM** (mensaje de canal, `<1.0`). Es el seguro contra alucinaciones y la defensa ante "¿y si alucina una fecha?". |
| 3 | Capa de bot delgada | Respondió *por qué eligió* Python, no *cómo mitiga* el riesgo | Mitigación = adaptador de bot sin lógica de negocio. Ignorarla implica: acoplamiento al SDK débil, imposibilidad de testear sin Teams y **muerte del plan de contingencia Angular**. |

**Patrón raíz identificado:** tendencia a razonar en términos de *rendimiento y técnica* cuando el problema es de *gobernanza, seguridad o riesgo*. Es el reflejo típico de un buen desarrollador que aún no piensa como arquitecto. Vigilar en cada OT.

**Aporte válido de Iker que se incorporó al plan:** el *bus factor* del equipo como criterio para elegir Python (ADR-001, razón 3). Buen argumento de arquitectura.

---

## Decisiones pendientes

- **F4.5 — Graph Explorer, aplazado a la próxima sesión (8-sep-2026):** ejecutar
  `GET /teams/{team-id}/channels/{channel-id}/messages` autenticado con la cuenta del tenant y
  anotar el resultado (200 con datos, o 403 + el permiso exacto que exige). Determina si la fuente
  `MENSAJE` va a necesitar RSC (Resource-Specific Consent). No bloquea el resto de F4 — el bot ya
  responde en Teams sin esto — pero hay que cerrarlo antes de dar por terminada la ✅ Compuerta F4.
- ⚠️ **15 sep — FECHA CRÍTICA:** vence la prueba de M365 Business Standard. Decidir pago
  (16,80 USD/mes) o migrar de tenant **antes** de esa fecha. Un tenant caído en octubre = sin demo.
- ⚠️ **30 sep — DISPARADOR ADR-009:** si no hay núcleo end-to-end, congelar Teams y priorizar la
  web responsive para asegurar la rúbrica.
- **Preguntar al docente** si un bot de Teams cuenta como *"implementación responsive (Desk y Mobile)"*.
  Un minuto de conversación elimina el riesgo más grande del proyecto.
- Verificar qué se entregó realmente en E2 (OKR/buyer persona), E3 (prototipo) y E4 (User Story
  Mapping + HU). Postergado por decisión del tech lead. **Riesgo R8.**
- Frontend en React (propuesta original) vs Angular (fortaleza de Iker). Decidir en F4.
- ¿Qué métrica exacta se usará para evaluar la calidad de las respuestas? (Definir antes de la demo.)

---

## Riesgos — actualización 2-sep-2026

| # | Riesgo | Estado |
|---|---|---|
| R4 | SDK de bot de Teams para Python inmaduro | 🟢 **CERRADO 2-sep.** `microsoft-teams-apps 2.0.16` es GA y corre sobre FastAPI. Riesgo residual: rotación de SDKs y poca documentación de terceros |
| R8 | **Entregables E2/E3/E4 del curso sin verificar** | 🔴 **Nuevo. Abierto por decisión del tech lead** |
| R9 | **Ventana real de 8 semanas, no 14** | 🔴 **Nuevo. Mitigado con recorte del RAG** |
| R10 | **Rúbrica exige responsive Desk+Mobile; el bot no lo cumple literalmente** | 🟡 **DEGRADADO (13-sep).** El tech lead reporta que se le explicó al docente la forma de trabajo y no hay problema. **Salvedad: acuerdo verbal, no escrito.** Mitigación recomendada: captura de `semana` en Teams **móvil** (OT-04 F6) + confirmación por correo. Disparador del 30-sep sigue vigente |
| R11 | **Tenant vence el 15-sep** | 🟡 **DEGRADADO de 🔴 a 🟡 (8-sep).** Decisión del tech lead: **no se paga; el tenant se reconstruye.** Con `RUNBOOK-TENANT.md` escrito, un tenant caído deja de ser un riesgo de proyecto y pasa a ser ~2 h de trabajo + 24 h de propagación. **Residual:** los pasos P6–P8 (bot, túnel, paquete) siguen sin ejecutarse ni documentarse; hasta OT-03A el runbook está incompleto en su tercio final |
| R12 | **Spike de Teams se conserva más allá de lo previsto** (decisión del tech lead, para demos a la profesora) | 🟡 **Nuevo (8-sep).** Revisar antes de la entrega final — el repo no debería llegar a sustentación con un spike desechable adentro |
| R13 | **El SDK de Teams no publica tipos (`py.typed` ni stubs)** | 🟡 **Nuevo (8-sep).** Verificado en `microsoft-teams-apps 2.0.16`. Bajo `mypy --strict` produce 7 errores. Mitigado con excepción acotada a `app.bot.bot_teams`. **El tamaño de esa excepción es la métrica de si la Capa de Bot Delgada sigue siendo delgada** |
| R14 | **Datos de configuración mal copiados: bugs silenciosos de latencia larga** | 🟢 **Nuevo (8-sep).** Detectado en `AZURE_TENANT_ID` (35 caracteres en vez de 36). Habría explotado en OT-05 con un error opaco. Se cierra con validación de formato GUID en `Configuracion` (OT-03A, Fase 1) |
| R15 | **Los usuarios finales no pueden consentir apps multiinquilino sin *verified publisher*** | 🟠 **Abierto (8-sep).** Afecta al modelo ISV (ADR-003). Requiere alta en Microsoft Partner Network. Documentado con honestidad en `GUIA-INSTALACION-TI.md` §7: se le dice al admin antes de que lo descubra en la pantalla de aprobación. **No bloquea el desarrollo en tenant propio** |
| R16 | **El manifiesto de Teams conserva la identidad del scaffold** (`My App, Inc.`, `example.com`) | 🟠 **Abierto (verificado el 13-sep: sigue así).** Teams **exige** URLs válidas de privacidad y términos para publicar. Se cierra en **OT-04 F0.2** |
| R18 | **Reglas de agente contradiciendo los ADR del proyecto** | 🟢 **CERRADO 13-sep.** Los 5 archivos de `.agents/rules/` reescritos para este repositorio. **Regla adoptada: las reglas de un agente son configuración de producción; si contradicen el repo, el agente no se equivoca, obedece** |
| R19 | **Sin CI** — el Definition of Done del propio tablero lo exige | 🟠 **Nuevo (13-sep).** `ruff` ha quedado en rojo al entregar **dos OT seguidas**, porque la compuerta depende de que alguien se acuerde. Se cierra en OT-04 F7.1 |
| R20 | **Paquetes del equipo sin avance desde el 23-ago** (golden dataset de Antonio, ingesta de Julián) | 🟠 **Nuevo (13-sep).** El golden dataset es la respuesta a la pregunta 3 de sustentación. Sin él no hay métrica de calidad |
| R17 | **`scripts/seed_tenant.py` necesitará permisos de escritura que Brújula no debe tener** | 🟡 **Nuevo (8-sep).** Mitigación decidida: **registro de app separado y de un solo inquilino** (`brujula-seed`), nunca distribuido. Añadir `ReadWrite` a la app de Brújula destruiría su argumento comercial ante un admin de TI |
## 14-oct-2026 — OT-06: precarga consentida de sugerencias

- OAuth renovable por usuario con estado de un solo uso, refresh tokens cifrados y revocación con
  `no vigilar`.
- Worker separado: solo usuarios con consentimiento, ventana de 7 días/300 mensajes y huella sin
  contenido para evitar llamadas repetidas a Gemini; `revisar` responde con la bandeja precargada.
- Pendiente: prueba real Entra/Graph tras el despliegue.
