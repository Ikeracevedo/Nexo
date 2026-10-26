# RUNBOOK — Reconstruir el entorno de Nexo desde cero

> **Para quién:** Iker (o quien herede el proyecto). **No** es la guía para clientes —
> esa es `GUIA-INSTALACION-TI.md`, y hace algo completamente distinto (ver §0.2).
> **Versión 1.0 — 8 de septiembre de 2026.** Se actualiza cada vez que se ejecuta.

---

## 0. Antes de empezar

### 0.1 Por qué existe este documento

El tenant de desarrollo (`brujulateams.onmicrosoft.com`) es una prueba de 30 días que vence el
**15-sep-2026**. La decisión del tech lead es **no pagar y reconstruir en un tenant nuevo cuando
haga falta.**

Esa decisión solo es sensata si la reconstrucción es un **procedimiento**, no una arqueología. Con
este runbook, un tenant caído deja de ser un riesgo de proyecto (R11) y pasa a ser dos horas de
trabajo. Sin él, es una tarde perdida reconstruyendo de memoria y descubriendo a las tres horas que
falta un permiso.

> **El principio que hay detrás, y vale para cualquier proyecto:** *un entorno que solo una persona
> sabe reconstruir es un punto único de fallo con forma de infraestructura.* Escribir el runbook no
> es documentación burocrática: es lo que convierte un riesgo en una tarea.

### 0.2 Este documento vs. la Guía de Instalación para TI

**No los mezcles.** Son públicos distintos y hacen cosas casi disjuntas.

| | Este runbook | `GUIA-INSTALACION-TI.md` |
|---|---|---|
| Lector | Tú, el proveedor | El admin de TI de una empresa cliente |
| ¿Crea un tenant? | Sí | **No.** Ya tiene el suyo |
| ¿Registra una app en Entra? | Sí | **No.** La app ya existe y es multiinquilino |
| ¿Genera secretos? | Sí | **Nunca.** El secreto es tuyo, no suyo |
| Qué hace el lector | 10 pasos | Aprobar un consentimiento e instalar la app |
| Objetivo | Reproducibilidad | Que te aprueben |

> **Por qué importa arquitectónicamente.** El modelo ISV (ADR-003) dice que el cliente instala tu
> software en su tenant. Si tu guía de cliente le pidiera registrar una aplicación, estarías
> confesando que no tienes un producto: tendrías un tutorial. **La brevedad de la guía de cliente
> es la demostración de que el modelo ISV funciona.**

### 0.3 Decisiones irreversibles — leer antes del primer clic

Estas cinco no se corrigen después sin rehacer trabajo:

| # | Decisión | Si te equivocas |
|---|---|---|
| 1 | **Tipos de cuenta compatibles = "Cuentas en cualquier directorio organizativo (multiinquilino)"** | El `CLIENT_ID` queda atado a tu tenant **para siempre**. Ninguna empresa cliente podría instalar Nexo. Hay que registrar una app nueva y reconfigurar todo |
| 2 | **Cuenta de tipo *work/school*, no de consumidor** | Las cuentas `@outlook.com`/`@hotmail.com` no tienen Teams empresarial, ni Planner, ni superficie útil de Graph. Todo el proyecto se queda sin sustrato |
| 3 | **Nombre del dominio `<algo>.onmicrosoft.com`** | No se renombra. Aparece en URLs, cuentas y capturas. Elige uno que no dé vergüenza en la sustentación |
| 4 | **La cuenta creadora queda como administrador global** | Ese rol no se delega por conveniencia. A los compañeros se les delega la siembra de datos, **nunca las llaves del tenant** (mínimo privilegio, ADR-002, aplicado puertas adentro) |
| 5 | **Solo permisos delegados de lectura. Ni un `ReadWrite`** | Un admin de TI que ve "escritura en tus chats" en la pantalla de consentimiento no aprueba. La lista de permisos **es** el argumento comercial |

### 0.4 Ruta crítica — el orden importa

**El paso 2 (habilitar carga de apps personalizadas) puede tardar hasta 24 horas en propagarse.**
Es lo único con espera real. Va primero, antes de escribir una línea de configuración, y mientras
propaga se hace todo lo demás.

```
P2 (24h de propagación)  ────────────────────────────────────┐
P1 → P3 → P4 → P5 → P6 → P7 → P8 ─────────────────────────→ P9 → P10
     (trabajo continuo, ~2 h)                                  (necesita P2 listo)
```

**Tiempo total:** ~2 h de trabajo efectivo + hasta 24 h de espera pasiva.

### 0.5 Qué NO transfiere entre tenants

Lo que se pierde al cambiar de tenant **no es código**: son datos y registros. Esta es la lista
completa, y es la razón de ser del runbook.

| Se pierde | Se reconstruye en |
|---|---|
| El registro de app de Entra ID (`CLIENT_ID`, secreto, redirect URIs, consentimientos) | P3–P5 |
| El registro del bot (`BOT_ID`, `BOT_PASSWORD`) y su endpoint | P6 |
| El paquete de app de Teams (`manifest.json` lleva el `botId`) | P8 |
| Usuarios de prueba | P9 |
| El plan de Planner y sus tareas | P9 |
| Los eventos de calendario | P9 |
| El equipo de Teams y sus canales | P9 |

**Lo que NO se pierde:** el código. Ni una línea. Ese es el requisito de arquitectura derivado de
OT-01 y se verifica en P10: *cambiar de tenant debe costar **solo variables de entorno**. Cero
identificadores de tenant escritos en el código.*

---

# P1 — Crear el tenant

**Tiempo:** ~20 min · **Costo:** gratis 30 días, luego 16,80 USD/usuario/mes

### Vías, en orden de preferencia

| Vía | Estado verificado el 23-ago-2026 |
|---|---|
| **Microsoft 365 Developer Program** (sandbox E5 gratuito) | ❌ *"You don't currently qualify for a Microsoft 365 Developer Program sandbox subscription."* Hoy exige suscripción Visual Studio **Professional o Enterprise** |
| Suscripción Visual Studio vía la universidad | ❌ La UPB solo da **Dev Essentials** (nivel gratuito). No califica |
| **M365 Business Standard — prueba de 30 días** | ✅ **La que funcionó.** Tenant real con Teams, Planner, To Do y Exchange |

> **Vuelve a intentar la vía 1 cada vez.** Los criterios del Developer Program cambian, y un
> sandbox E5 gratuito y renovable resolvería R11 de forma permanente. Cuesta dos minutos comprobarlo
> y ahorraría el ciclo entero de reconstrucción.

### Qué anotar

```
Dominio:            <algo>.onmicrosoft.com
Organización:       ...
Cuenta admin:       ...@<algo>.onmicrosoft.com
Fecha de creación:  ...
FECHA DE VENCIMIENTO DE LA PRUEBA: ...   ← al calendario, con alarma a 3 días
```

### ⚠️ Riesgo conocido

Encadenar pruebas gratuitas sucesivas es frágil: Microsoft las ata al método de pago, al teléfono y
al dominio. **No construyas el cronograma sobre eso.** Si la sustentación depende de un tenant vivo,
el tenant de la sustentación se crea con margen, no la víspera.

### ✅ Compuerta

- [ ] Sesión iniciada en `admin.cloud.microsoft` con la cuenta nueva
- [ ] La cuenta aparece como **administrador global**
- [ ] Teams abre y Planner está disponible

---

# P2 — Habilitar carga de apps personalizadas ⏱️ RUTA CRÍTICA

**Tiempo:** 2 min de clics + **hasta 24 h de propagación** · **Hazlo inmediatamente después de P1**

**Centro de administración de Teams** → *Aplicaciones de Teams* → **Directivas de configuración**
→ **Global (predeterminada para toda la organización)** → *"Cargar aplicaciones personalizadas"* =
**Activado** → **Guardar**.

### Qué anotar

```
Directiva guardada a las:  <hora exacta>   ← la propagación se cuenta desde aquí
```

### Cómo verificar que propagó

Teams (cliente de escritorio o web, con la cuenta del tenant) → **Aplicaciones** → *Administrar tus
aplicaciones* → debe aparecer **"Cargar una aplicación personalizada"**.

Si no aparece: cerrar sesión completamente en Teams y volver a entrar (el cliente cachea la
directiva). Si sigue sin aparecer, seguir esperando y continuar con P3.

> **Este es el paso que la primera vez costó seis días de retraso**, porque se hizo tarde y luego
> el sideload quedó pendiente sesión tras sesión. **La lección operativa: en cualquier montaje,
> identifica primero qué tiene latencia externa y dispáralo antes que nada.** Lo que espera solo,
> que espere mientras tú trabajas.

---

# P3 — Registrar la aplicación en Entra ID

**Tiempo:** 5 min

`entra.microsoft.com` → **Identidad** → **Aplicaciones** → **Registros de aplicaciones** →
**Nuevo registro**.

| Campo | Valor |
|---|---|
| Nombre | `Nexo` |
| Tipos de cuenta compatibles | ⚠️ **Cuentas en cualquier directorio organizativo (multiinquilino)** — decisión irreversible #1 |
| URI de redirección | Plataforma **Web** → `http://localhost:8000/auth/callback` |

### Qué anotar (del **Overview**)

```
Application (client) ID:   ........-....-....-....-............   (36 caracteres)
Directory (tenant) ID:     ........-....-....-....-............   (36 caracteres)
Object ID:                 ........-....-....-....-............
Supported account types:   debe decir "Multiple organizations"
```

### 📸 Evidencia a capturar

1. La pantalla de **Overview** mostrando *Supported account types: **Multiple organizations***.
   Es la prueba documental del ADR-003.

### ⚠️ Trampa verificada el 8-sep-2026

**Cuenta los caracteres de los GUID que pegues.** Un GUID tiene exactamente **36**. En la primera
configuración, `AZURE_TENANT_ID` quedó con 35 — se perdió el primer carácter al copiar. No rompió
nada durante días, porque nada leía esa variable todavía; habría explotado semanas después contra
Microsoft con un error opaco.

Desde OT-03A, `app/config.py` valida el formato y la aplicación **se niega a arrancar** si un
identificador está mal. Aun así, cuéntalos: la validación es la red de seguridad, no la excusa.

---

# P4 — Permisos delegados y consentimiento

**Tiempo:** 10 min

**API permissions** → *Add a permission* → **Microsoft Graph** → **Delegated permissions**:

| Permiso | Qué habilita | Alimenta `FuentePendiente` |
|---|---|---|
| `User.Read` | Identidad del usuario | — (contexto) |
| `Calendars.Read` | Eventos del calendario propio | `CALENDARIO` |
| `Tasks.Read` | To Do **y** Planner (permiso compartido) | `TODO`, `PLANNER` |
| `Team.ReadBasic.All` | Nombres y descripciones de los equipos del usuario | previo a `MENSAJE` |
| `Chat.Read` | Contenido de chats 1-a-1 y grupales | `MENSAJE` |

Después: **Grant admin consent for \<tu tenant\>** y verificar que las cinco filas quedan en
**✅ Granted**.

> **Verifica en la tabla, no asumas por el redirect.** Que el portal te devuelva a la página no
> significa que el consentimiento se aplicó. La columna *Status* es la única fuente de verdad.
> (Esto ya se hizo bien en la primera configuración; queda escrito para que se siga haciendo.)

### 📸 Evidencia a capturar

2. La tabla de **API permissions** con las 5 filas, `Delegated`, todas *Granted*, y **ningún
   `ReadWrite`**.

### Modelo mental — `Recurso.Acción.Alcance`

El sufijo **`.All`** es la frontera entre *"leo lo mío"* y *"leo lo de la organización"*, y es lo
que dispara el requisito de consentimiento de administrador. `Team.ReadBasic.All` es el único con
`.All` en esta lista, y se puede consentir **porque eres admin global de tu propio tenant**.

> En el tenant de la UPB ese permiso sería inalcanzable — de hecho, allí ni siquiera los permisos
> personales (`Calendars.Read`, `Tasks.Read`, `Chat.Read`) se pueden consentir, porque la
> universidad tiene deshabilitado el consentimiento de usuario. **Ese hallazgo es la validación
> empírica del ADR-003**, y por eso el desarrollo va sobre tenant propio.

### 🔴 Advertencia del portal, pendiente de resolver (R15)

Entra advierte: *"End users cannot grant consent to newly registered multitenant apps without
verified publishers."*

Significa que, en un tenant cliente, **un usuario normal no podrá autorizar Nexo por su cuenta**
mientras la app no tenga *Verified Publisher*. Solo el admin podrá. Para desarrollo propio no
bloquea nada (eres admin). Para el modelo ISV **sí importa**, y requiere alta en el Microsoft
Partner Network. Va documentado en la Guía de Instalación.

---

# P5 — Secreto de cliente

**Tiempo:** 2 min · **⏰ Vence**

**Certificates & secrets** → *New client secret* → descripción `brujula-dev`, expiración
**6 meses**.

### ⚠️ Dos trampas

1. **El valor solo se muestra una vez.** Cópialo inmediatamente. Si lo pierdes, se genera otro.
2. El portal muestra un **Secret ID** y un **Value**. El que va al `.env` es el **Value**. El
   *Secret ID* no sirve para autenticarse. Confundirlos cuesta una hora.

### Al `.env` (nunca al repositorio)

```bash
AZURE_TENANT_ID=<Directory (tenant) ID>
AZURE_CLIENT_ID=<Application (client) ID>
AZURE_CLIENT_SECRET=<el Value del secreto>
AZURE_REDIRECT_URI=http://localhost:8000/auth/callback
```

### Verificación obligatoria

```powershell
git check-ignore -v .env
git status          # .env NO debe aparecer
```

Si `git check-ignore` no devuelve nada, **detente y arréglalo antes de seguir**. Un secreto
commiteado en un repo público no se borra con otro commit: hay que **rotarlo**, porque ya está en
el historial y en los mirrors.

> **Y lee cuál regla hizo el match.** En la primera configuración, `env/.env.local.user` quedó
> protegido por la regla `ENV/` en mayúsculas, que coincidió **solo porque Windows no distingue
> mayúsculas de minúsculas**. En Linux —es decir, en cualquier CI— no habría coincidido. *Estar
> protegido no es lo mismo que estar protegido a propósito.*

### 📅 Anotar el vencimiento

```
Secreto creado:   ...
VENCE:            ...  (+6 meses)   ← al calendario
```

---

# P6 — Registro del bot

**Tiempo:** ~15 min · **Estado: pendiente de ejecutar en OT-03A, Fase 4**

El bot tiene una identidad **distinta** de la app de Entra ID de P3. Son dos registros:

| Registro | Para qué | Variables |
|---|---|---|
| App de Entra ID (P3) | Leer datos del usuario vía Microsoft Graph | `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET` |
| Registro de bot (P6) | Que Bot Framework enrute mensajes de Teams a tu endpoint | `TEAMS_BOT_ID`, `TEAMS_BOT_PASSWORD` |

> Confundirlos es un clásico. Uno responde *"¿quién es el usuario y qué puede ver?"*; el otro,
> *"¿a qué URL le mando los mensajes y cómo sé que el bot es quien dice ser?"*

**Messaging endpoint:** `https://<tu-túnel>/api/messages` (se obtiene en P7).

### Qué anotar

```
TEAMS_BOT_ID=
TEAMS_BOT_PASSWORD=
Messaging endpoint configurado:
```

> ⏳ **Sección a completar tras ejecutar OT-03A Fase 4.** Rellena aquí la vía exacta que
> funcionó (Azure Bot, `dev.botframework.com`, o el provisionamiento del Agents Toolkit), con sus
> clics. **Escríbelo el mismo día que lo hagas**, no después: los detalles de portal se olvidan en
> una semana.

---

# P7 — Túnel de desarrollo

**Tiempo:** ~10 min · **Estado: pendiente de ejecutar en OT-03A, Fase 4**

Teams necesita una URL pública HTTPS que llegue a tu `localhost:8000`.

**Decisión de diseño: túnel persistente, no efímero.** Un túnel efímero cambia de URL en cada
arranque, y cada cambio obliga a editar el endpoint del registro de bot. Eso es **una dependencia
externa dentro del ciclo de iteración**, justo lo que la regla adoptada en OT-01 prohíbe. Con un
túnel persistente, la URL se configura una vez y no vuelve a cambiar: iterar es reiniciar
`uvicorn`.

```powershell
devtunnel user login
devtunnel create brujula-dev --allow-anonymous
devtunnel port create brujula-dev -p 8000
devtunnel host brujula-dev
```

> ⏳ **A verificar y corregir tras OT-03A.** Los subcomandos exactos pueden variar. Si `devtunnel`
> se resiste más de 20 minutos, usa `F5` del Agents Toolkit para no perder la evidencia, y deja el
> túnel persistente como mejora posterior. **No se sacrifica la entrega por la elegancia de la
> herramienta.**

### Qué anotar

```
URL pública del túnel:  https://........devtunnels.ms
¿Persistente?           sí / no
```

---

# P8 — Paquete de app de Teams

**Tiempo:** ~15 min · **Estado: pendiente de ejecutar en OT-03A, Fase 4**

Un `.zip` con `manifest.json` + dos iconos PNG (color y outline), **con los archivos en la raíz del
zip**, no dentro de una carpeta.

### Campos del manifiesto que hay que rellenar de verdad

El scaffold del Toolkit deja marcadores de posición. Estos **no se dejan como están**:

| Campo | Valor del scaffold | Qué poner |
|---|---|---|
| `name.short` / `name.full` | `teams-hello…` | `Nexo` / nombre real |
| `description.short` / `.full` | *"short description for teams-hello"* | La descripción real del producto |
| `bots[0].botId` | `${{BOT_ID}}` | Tu `TEAMS_BOT_ID` de P6 |
| `developer.name` | **`My App, Inc.`** | Tu nombre / el del equipo |
| `developer.websiteUrl` | **`https://www.example.com`** | URL real |
| `developer.privacyUrl` | **`https://www.example.com/privacy`** | URL real |
| `developer.termsOfUseUrl` | **`https://www.example.com/termofuse`** | URL real |

> ⚠️ **Los tres campos de `developer` con `example.com` son un problema real, no cosmético.** Teams
> exige URLs válidas de política de privacidad y términos de uso para publicar una app, y un admin
> de TI que abra el manifiesto y vea `My App, Inc.` no aprueba nada. **Es lo primero que mira quien
> evalúa si una app es legítima o phishing.**
>
> Es el mismo hallazgo que la bitácora ya registró sobre el `requirements.txt` generado: *confiar
> en un scaffold es heredar las decisiones de otro sin haberlas revisado.* Aquí las decisiones
> heredadas son la identidad de tu producto.

`bots[0].scopes` = `["personal", "team", "groupChat"]` — los tres sirven; `personal` es el que usa
la demo.

### Qué anotar

```
Ruta del paquete en el repo:   teams/appPackage/
Nombre del zip generado:
```

---

# P9 — Sembrar datos de prueba

**Tiempo:** ~30 min a mano · **~1 min con script (pendiente de escribir)**

Un tenant recién creado está **vacío**. Las seis llamadas de Graph responden `200 OK` con
`"value": []`, que es correcto pero no demuestra nada. Sin datos no hay demo.

### Mínimo para una demo creíble

| Qué | Dónde | Para qué |
|---|---|---|
| 1 equipo de Teams con 1–2 canales | Teams | `Team.ReadBasic.All`, y el contenedor de la fuente `MENSAJE` |
| 1 plan de Planner con 3–4 tareas, con fechas dentro de los próximos 7 días | Planner | Fuente `PLANNER` |
| 3–4 tareas en To Do, alguna **sin fecha** | To Do | Fuente `TODO` — y el caso borde de `vence=None` |
| 2–3 eventos de calendario en la semana | Outlook | Fuente `CALENDARIO` |
| 2–3 mensajes en un canal que *parezcan* asignar una tarea | Teams | Fuente `MENSAJE`, la que se infiere con `confianza < 1.0` |

> **Los datos de siembra no son de relleno: son el guion de la demo.** Diseña las fechas para que
> la respuesta a *"¿qué tengo esta semana?"* se vea bien —algo hoy, algo mañana, algo sin fecha— y
> para que el mensaje de canal sea genuinamente ambiguo. Un pendiente inferido al 72% solo es
> convincente si el mensaje original de verdad es ambiguo.

### `scripts/seed_tenant.py` — especificación (pendiente)

Mitigación acordada en OT-01. Convierte 30 minutos de clics en un comando, hace los tests
reproducibles y es un artefacto de portafolio por sí solo.

| Recurso | Endpoint de Graph | Permiso necesario (escritura, **solo para el script**) |
|---|---|---|
| Equipo de Teams | `POST /teams` | `Team.Create` |
| Canal | `POST /teams/{id}/channels` | `Channel.Create` |
| Plan de Planner | `POST /planner/plans` | `Tasks.ReadWrite` |
| Tarea de Planner | `POST /planner/tasks` | `Tasks.ReadWrite` |
| Tarea de To Do | `POST /me/todo/lists/{id}/tasks` | `Tasks.ReadWrite` |
| Evento | `POST /me/events` | `Calendars.ReadWrite` |
| Mensaje de canal | `POST /teams/{id}/channels/{id}/messages` | `ChannelMessage.Send` |

> ⚠️ **Decisión de seguridad que hay que tomar y no improvisar.** El script necesita permisos de
> **escritura** que Nexo **no tiene ni debe tener**. La regla del ADR-002 —cero `ReadWrite`— es
> el argumento comercial del producto.
>
> **La solución correcta: un registro de app SEPARADO**, llamado por ejemplo `brujula-seed`,
> **de un solo inquilino**, que exista solo en tu tenant de desarrollo y no se distribuya jamás.
> Nexo conserva sus cinco permisos de lectura intactos.
>
> **La solución incorrecta**, y es tentadora porque ahorra diez minutos: añadir los `ReadWrite` a la
> app de Nexo "solo para sembrar". Eso mete permisos de escritura en la pantalla de
> consentimiento que ve el admin de TI del cliente, y **destruye el argumento más fuerte del
> producto** para ahorrarte un registro. No lo hagas.

Estado: **sin escribir.** No se entrega código sin verificarlo, y verificarlo requiere un tenant
donde ejecutarlo. Se escribe en la sesión en que se reconstruya el tenant, que es cuando se puede
probar de verdad.

---

# P10 — Verificación final

**Tiempo:** ~15 min. **Es la compuerta: sin esto, el tenant no está listo.**

### 10.1 Batería de Graph Explorer

`developer.microsoft.com/graph/graph-explorer`, autenticado con la cuenta del tenant:

```
GET https://graph.microsoft.com/v1.0/me
GET https://graph.microsoft.com/v1.0/me/events
GET https://graph.microsoft.com/v1.0/me/todo/lists
GET https://graph.microsoft.com/v1.0/me/planner/tasks
GET https://graph.microsoft.com/v1.0/me/joinedTeams
GET https://graph.microsoft.com/v1.0/me/chats
```

**Las seis deben responder `200 OK`, y con datos** (después de P9). Si alguna da `403`, el
problema son los **scopes del token de Graph Explorer**, no los privilegios de la cuenta: Graph
Explorer arranca con el mínimo (`openid, profile, User.Read, email`) y hay que consentir los demás
desde su propio panel de permisos.

> Ese fue exactamente el hallazgo de OT-01: al primer intento **solo `/me` respondió 200** y las
> otras cinco dieron 403. La causa no era la cuenta ni el tenant. **Faltaban los scopes, no los
> privilegios.** Guárdalo: te ahorra media hora de pánico.

### 10.2 La llamada que decide el diferenciador del producto

```
GET /me/joinedTeams
GET /teams/{team-id}/channels
GET /teams/{team-id}/channels/{channel-id}/messages     ← ¿200 o 403?
```

`Chat.Read` cubre chats 1-a-1 y grupales. Los mensajes de **canal** van por
`ChannelMessage.Read.All`, que es *Protected API*. Y es ahí donde vive el contenido académico: el
anuncio del profesor en el canal de la materia — **la fuente `MENSAJE`**, el pendiente amarillo, lo
que distingue a Nexo de un agregador tonto.

Si sale `403`, la vía es **RSC** (*Resource-Specific Consent*): el dueño del equipo autoriza la app
sobre **ese** equipo, sin pasar por el admin del tenant. Encaja con el modelo ISV y con que tú eres
dueño de los equipos de tu propio tenant.

**Anota el resultado. Sigue pendiente desde el 2-sep.**

### 10.3 La verificación que prueba la arquitectura

Esta es la que convierte el runbook en evidencia de diseño:

```powershell
# 1. Actualizar SOLO el .env con los identificadores del tenant nuevo
# 2. Sin tocar una linea de codigo:
uvicorn app.main:app --reload --port 8000
pytest
```

**Si arranca y los tests pasan sin haber modificado código, el requisito de OT-01 se cumple:**
*cambiar de tenant cuesta solo variables de entorno.*

> **Esto no es una comprobación rutinaria: es la prueba empírica de una promesa de arquitectura.**
> Cuando el docente pregunte *"¿qué tan acoplado está su sistema a Microsoft?"*, la respuesta no es
> un diagrama: es *"cambié de tenant entero y solo toqué el `.env`; aquí está el runbook y aquí el
> `git diff` vacío."*
>
> Y si **no** arranca, acabas de encontrar un identificador escrito a fuego en el código. Búscalo y
> muévelo a `config.py`. El runbook es también un test de acoplamiento.

### ✅ Compuerta final del runbook

- [ ] Las 6 llamadas de Graph en `200 OK` **y con datos**
- [ ] Resultado de la llamada de mensajes de canal anotado (200 o 403 + permiso exigido)
- [ ] `uvicorn app.main:app` arranca solo con el `.env` cambiado
- [ ] `pytest` verde
- [ ] El bot responde en Teams
- [ ] Evidencia capturada (mínimo las 2 de P3 y P4, más las de Teams)
- [ ] Fechas de vencimiento en el calendario

---

# Anexo A — Qué se puede automatizar y qué no

| Paso | ¿Automatizable? | Por qué |
|---|---|---|
| P1 Crear tenant | ❌ No | Alta comercial con verificación de pago y teléfono. Clics irreducibles |
| P2 Directiva de sideload | ⚠️ Parcial | Existe API de directivas de Teams, pero requiere PowerShell con módulo de Teams y credenciales de admin. Para una vez cada varios meses, no compensa |
| P3 Registrar app de Entra | ✅ Sí | `az ad app create` o Graph `POST /applications`. **Vale la pena**: es el paso con la decisión irreversible más cara |
| P4 Permisos + consentimiento | ⚠️ Parcial | Los permisos se asignan por API; el *admin consent* interactivo, no siempre |
| P5 Secreto | ✅ Sí | `az ad app credential reset` |
| P6 Registro de bot | ⚠️ Parcial | El Agents Toolkit lo hace con `botFramework/create`. A mano también |
| P7 Túnel | ✅ Sí | `devtunnel` es CLI de principio a fin |
| P8 Paquete de app | ✅ Sí | Generar `manifest.json` desde plantilla + comprimir. 20 líneas de Python |
| P9 Sembrar datos | ✅ **Sí, y es lo que más rinde** | `scripts/seed_tenant.py`. 30 min → 1 comando, y hace los tests reproducibles |
| P10 Verificación | ✅ Sí | Un script que ejecute la batería de Graph y reporte una tabla |

> **Dónde invertir, si solo puedes automatizar una cosa: P9.** Es el que más tiempo consume, el
> único que hay que repetir a menudo (no solo al cambiar de tenant: cada vez que quieras un estado
> limpio para probar), y el único cuyo resultado usan los tests. Los demás se ejecutan una vez cada
> varios meses; automatizarlos es optimizar lo que no duele.

---

# Anexo B — Fechas que vencen

| Qué | Vence | Consecuencia |
|---|---|---|
| Prueba de M365 Business Standard | 30 días desde P1 | El tenant deja de funcionar. Reconstruir con este runbook o pagar 16,80 USD/usuario/mes |
| Secreto de cliente | 6 meses desde P5 | La autenticación deja de funcionar con un error de credenciales. **Es el fallo más desconcertante posible**: nada cambió en el código y todo dejó de andar |
| Túnel de desarrollo | Depende de la vida de la sesión, salvo que sea persistente | El bot deja de recibir mensajes. Se nota al instante |

**Los tres, al calendario, con alarma tres días antes.** El del secreto especialmente: es el único
que rompe el sistema sin que nada visible haya cambiado.

---

# Anexo C — Cómo se mantiene este documento

**Regla:** cada vez que se ejecute un paso de este runbook, se corrige el paso el mismo día — no
después. Un runbook que no se actualiza al usarlo se convierte en ficción en dos iteraciones, y un
runbook en el que ya no se confía es peor que no tenerlo, porque alguien lo va a seguir de todos
modos.

**Secciones marcadas ⏳ pendientes de completar tras ejecutar OT-03A Fase 4:** P6, P7 y P8.

**Y al terminar la reconstrucción, anota lo que salió distinto de lo escrito.** Esa diferencia es
la información más valiosa del documento: es lo que cambió en las plataformas de Microsoft desde la
última vez, y es exactamente lo que se te habrá olvidado la próxima.
