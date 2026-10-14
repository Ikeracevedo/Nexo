# Guía de operación — levantar Brújula en desarrollo

> **Para quién:** quien va a arrancar el proyecto en su máquina en el día a día — venv, túnel,
> `uvicorn` — para desarrollar o hacer una demo. **No** es para crear infraestructura de Microsoft
> desde cero (tenant, registro de app, registro de bot): eso es `RUNBOOK-TENANT.md`. Esta guía
> asume que esa infraestructura **ya existe** y solo hay que encenderla.
>
> Si el tenant venció o hay que reconstruirlo, primero `RUNBOOK-TENANT.md`, y cuando ese runbook
> termine con un `TEAMS_BOT_ID` y un `AZURE_TENANT_ID` nuevos, se vuelve aquí.

---

## 0. Mapa mental: qué piezas hay y cómo se conectan

```
Teams (cliente del usuario)
    │  mensajes ("semana", "ayuda")
    ▼
Azure Bot Service  ──── conoce el Messaging endpoint ────┐
    │  reenvía HTTPS                                     │
    ▼                                                     │
devtunnel (URL pública)  ←── esta URL es la que cambia ──┘  si el túnel no es persistente
    │  reenvía a localhost
    ▼
uvicorn (tu máquina, puerto 8000)
    │
    ▼
app.main:app (FastAPI) ── monta los dos canales:
    ├── /api/agenda        (REST, se prueba con el navegador o curl)
    └── /api/messages      (Teams, lo llama Azure Bot Service, no tú directamente)
```

**Tres procesos tienen que estar vivos a la vez** para que el bot responda en Teams: el túnel,
`uvicorn`, y — indirectamente — Azure Bot Service, que no arrancas tú, ya está corriendo en la nube
de Microsoft todo el tiempo.

**La pieza que se rompe con más frecuencia es el túnel**, porque su URL pública puede cambiar. La
sección 5 explica exactamente qué hacer cuando pasa.

---

## 1. Requisitos, una sola vez por máquina

- Python 3.12.
- `devtunnel` CLI instalado y en el `PATH`. Verificar con:
  ```powershell
  devtunnel --version
  ```
  Si no está instalado:
  ```powershell
  winget install Microsoft.devtunnel
  ```
  Si `winget` tampoco está disponible, descarga directa:
  ```powershell
  mkdir C:\devtunnel
  Invoke-WebRequest -Uri https://aka.ms/TunnelsCliDownload/win-x64 -OutFile C:\devtunnel\devtunnel.exe
  $env:Path += ";C:\devtunnel"     # solo dura la sesión de PowerShell; para que sea permanente,
                                    # añadir C:\devtunnel a la variable de entorno Path del sistema
  ```
- Una cuenta para iniciar sesión en `devtunnel` (puede ser una cuenta personal de Microsoft, **no**
  tiene que ser la del tenant de Brújula — el túnel es infraestructura de desarrollo tuya, no del
  producto). Sesión ya iniciada:
  ```powershell
  devtunnel user login
  ```
  Si el login se queda pensando sin avanzar: probablemente se abrió el diálogo con la cuenta
  equivocada. Ciérralo, y en el picker de cuentas elige explícitamente una cuenta personal ya
  reconocida por Windows en vez de "agregar cuenta nueva".

---

## 2. Preparar el entorno del proyecto (una vez, o cuando cambien las dependencias)

Desde la raíz del repo:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
```

`requirements-dev.txt` ya incluye `requirements.txt` (`-r requirements.txt`), así que ese único
comando instala tanto las dependencias de producción como las de desarrollo (`pytest`, `ruff`,
`mypy`).

### El archivo `.env`

Copia `.env.example` a `.env` si todavía no existe, y complétalo con los valores reales (nunca se
sube al repo — está en `.gitignore`):

```
AZURE_TENANT_ID=          # Directory (tenant) ID del registro en Entra — RUNBOOK-TENANT.md P3
AZURE_CLIENT_ID=          # Application (client) ID del mismo registro           — P3
AZURE_CLIENT_SECRET=      # Secreto de cliente generado                         — P5
TEAMS_BOT_ID=             # Microsoft App ID del registro del BOT (Azure Bot)   — P6
TEAMS_BOT_PASSWORD=       # Client secret del registro del bot                  — P6
```

**`app/config.py` valida el formato de cada GUID al arrancar** y la aplicación se niega a levantar
si alguno está mal copiado (por ejemplo, con 35 caracteres en vez de 36). Si `uvicorn` falla al
arrancar con un `ValidationError` mencionando alguno de estos campos, el problema está en el
`.env`, no en el código — cuenta los caracteres del valor que pegaste.

> **Nota sobre `TEAMS_BOT_ID` vs `AZURE_CLIENT_ID`:** son dos identidades distintas de dos registros
> distintos en Azure. `AZURE_CLIENT_ID` es el registro de Entra ID que usa Microsoft Graph para leer
> datos del usuario. `TEAMS_BOT_ID` es el registro del Azure Bot que usa Bot Framework para enrutar
> mensajes de Teams a tu endpoint. Confundirlos es el error más común al reconstruir el entorno.

---

## 3. Arrancar todo (rutina de cada sesión de trabajo)

Se necesitan **dos terminales abiertas al mismo tiempo**. Ninguna de las dos puede cerrarse mientras
se quiera usar el bot en Teams.

### Terminal 1 — el túnel

```powershell
devtunnel host brujula-dev
```

Esto imprime la URL pública del túnel, algo como:

```
Connect via browser: https://<algo-generado>.devtunnels.ms
```

Copia esa URL. Si es la primera vez que se levanta este túnel en la máquina, o si cambió respecto a
la última vez, ve a la **sección 5** antes de continuar — hay que actualizar Azure con la URL nueva.

Deja esta terminal abierta y corriendo. No se le escribe nada más.

### Terminal 2 — el servidor de la aplicación

```powershell
.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload
```

Con `--reload`, cualquier cambio guardado en el código reinicia el servidor solo — no hace falta
parar y volver a lanzar `uvicorn` en cada edición.

Confirmación de que arrancó bien: en la terminal debe verse `Application startup complete.` y
`Uvicorn running on http://127.0.0.1:8000`.

### Verificación rápida sin usar Teams

```powershell
# en una tercera terminal, o en el navegador
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/api/agenda
```

`/health` debe responder `200` con un JSON `{"estado": "ok", ...}`. Si esto falla, el problema es
local (venv, `.env`, un error de código) y todavía no tiene nada que ver con Teams ni con el túnel
— resuélvelo aquí antes de seguir.

### Probar el bot en Teams

Con las dos terminales corriendo y la URL del túnel ya configurada en Azure (sección 5), abre un
chat con **Brújula** en Teams y escribe:

```
ayuda
semana
```

`ayuda` debe responder con la lista de comandos. `semana` debe responder con la tarjeta de
pendientes. Un mensaje fuera de alcance (por ejemplo, "dame una receta de pasta") debe recibir el
mensaje de "Brújula solo responde sobre tus pendientes".

---

## 4. Apagar todo

`Ctrl+C` en cada una de las dos terminales. No hay ningún otro proceso en segundo plano que limpiar
en el uso normal.

Si al volver a arrancar `uvicorn` aparece `[Errno 10048] error while attempting to bind on address`
(el puerto 8000 ya está en uso), casi siempre es un proceso de `uvicorn` de una sesión anterior que
no se cerró bien. Dos formas de resolverlo:

```powershell
# Opción A: encontrar y cerrar el proceso viejo
netstat -ano | findstr :8000
taskkill /PID <el-pid-que-aparece> /F

# Opción B: usar otro puerto mientras tanto (recuerda actualizar el messaging endpoint si el
# puerto usado localmente afecta a algo detrás del túnel — normalmente no, porque el túnel
# apunta al puerto, así que si cambias el puerto aquí, cambia también el `devtunnel port create`)
uvicorn app.main:app --reload --port 8001
```

---

## 5. Qué hacer si la URL del túnel cambia

Esto es lo que rompe el bot con más frecuencia y de forma menos obvia: **todo sigue funcionando en
local** (`/health` responde bien, `uvicorn` no muestra ningún error), pero Teams deja de recibir
respuestas, porque Azure Bot Service le sigue enviando los mensajes a una URL que ya no existe.

### Por qué cambia

Un túnel **efímero** genera una URL nueva cada vez que se destruye y se vuelve a crear. Un túnel
**persistente** (creado una vez con un nombre fijo, como `brujula-dev`) mantiene la misma URL entre
sesiones de `devtunnel host` — es la razón por la que este proyecto usa un túnel con nombre en vez
de uno efímero. Aun así, la URL puede cambiar si:

- El túnel se borró y se volvió a crear (`devtunnel delete` seguido de `devtunnel create`).
- Se está trabajando desde una máquina distinta, con un túnel distinto.
- Pasó el tiempo de vida máximo de un túnel gratuito y hubo que recrearlo.

### Cómo saber la URL actual

```powershell
devtunnel show brujula-dev
```

o simplemente mirar la línea `Connect via browser:` que imprime `devtunnel host brujula-dev` al
arrancar.

### Cómo actualizarla donde importa

La URL del túnel tiene que coincidir en **un único lugar de Azure**: el *Messaging endpoint* del
registro del bot.

1. Ve a [portal.azure.com](https://portal.azure.com) → busca el recurso del **Azure Bot** de
   Brújula (no el "tic1" de las pruebas iniciales — el bot dedicado creado en OT-03A).
2. **Configuration** (en el menú lateral del recurso).
3. Campo **Messaging endpoint** → reemplázalo por:
   ```
   https://<la-url-actual-del-tunel>.devtunnels.ms/api/messages
   ```
   **No se te olvide el `/api/messages` al final** — es la ruta que `crear_bot_teams()` monta sobre
   el núcleo de FastAPI (`app/bot/bot_teams.py`), no la raíz del túnel.
4. **Save.**
5. Vuelve a probar `ayuda` en Teams. No hace falta reinstalar la app ni tocar el `manifest.json` —
   el manifiesto no contiene la URL del túnel, solo el `botId`, que no cambia.

**Nada de esto toca `.env` ni el código.** El único identificador que cambia es la URL del túnel, y
vive únicamente en la configuración del recurso de Azure Bot — es justo el mismo principio que exige
`RUNBOOK-TENANT.md` para el resto del sistema: la infraestructura externa se reconfigura desde
afuera, nunca escribiéndola en el código.

---

## 6. Diagnóstico cuando el bot no responde en Teams

Sigue este orden — cada paso descarta una causa antes de pasar a la siguiente.

**1. ¿`/health` responde en local?**
No → el problema es local (venv, `.env`, código). Resuélvelo antes de mirar Teams.

**2. ¿El túnel sigue corriendo y su URL coincide con la de Azure?**
Revisa la terminal del túnel. Compara la URL que muestra con la que está guardada en *Messaging
endpoint* (sección 5). Si no coinciden, ese es el problema.

**3. ¿Aparece algo en la terminal de `uvicorn` cuando escribes en Teams?**

- **Nada aparece:** el mensaje no está llegando — el problema está entre Teams, Azure Bot Service y
  el túnel (revisa 1 y 2). `uvicorn --log-level debug` no ayuda aquí, porque el problema ni siquiera
  llegó a tu proceso.
- **Aparece un `200 OK` para `conversationUpdate` pero nada para los mensajes de texto, o aparece
  un `500`:** el mensaje sí está llegando. El problema está dentro de la aplicación. Sigue al
  siguiente punto.

**4. El error 500 no muestra traceback en la consola de `uvicorn`.**

Esto pasó una vez en este proyecto: el SDK de Teams registra sus propios errores con el módulo
`logging` de Python, pero por defecto esos mensajes no se propagan a la salida de `uvicorn`.
`uvicorn --log-level debug` **no resuelve esto** — ese flag controla el logging del propio
`uvicorn`, no el de las librerías que corren dentro de la aplicación.

La solución es forzar el nivel de logging de la aplicación entera, temporalmente, agregando esto en
`app/main.py` (arriba de `crear_app`):

```python
import logging

logging.basicConfig(level=logging.DEBUG)
```

Vuelve a mandar el mensaje en Teams y ahora sí debería verse el traceback completo en la consola de
`uvicorn`. **Quita estas dos líneas en cuanto termines de diagnosticar** — no deben quedar en el
código que se entrega ni en producción: generan un volumen de logs enorme y pueden filtrar detalles
de tokens/errores de autenticación en texto plano.

**5. El traceback dice `AADSTS700016` o `unauthorized_client`.**

Significa que el `App(...)` del SDK está pidiendo el token de autenticación contra el tenant
equivocado. Revisa en `app/bot/bot_teams.py` que `crear_bot_teams` le esté pasando
`tenant_id=config.azure_tenant_id` al construir el `App`. Si el registro del bot en Azure es
**Single Tenant** (no *Multi Tenant*), este parámetro es obligatorio — sin él, el SDK asume
multi-tenant por defecto y pide el token contra un endpoint genérico que no reconoce tu app.

**6. Al instalar la app en Teams aparece "Invalid Bot: Please make sure the bot is registered and
Teams channel is enabled".**

El recurso de Azure Bot no tiene el canal de **Microsoft Teams** habilitado (por defecto solo trae
"Web Chat"). En el recurso del bot → **Channels** → agregar **Microsoft Teams**.

---

## 7. Checklist de una sesión de demo

- [ ] `devtunnel host brujula-dev` corriendo, URL anotada.
- [ ] URL del túnel coincide con el *Messaging endpoint* del Azure Bot (sección 5) — verificar
      **antes** de la demo, no durante.
- [ ] `uvicorn app.main:app --reload` corriendo sin errores.
- [ ] `curl http://127.0.0.1:8000/health` responde `200`.
- [ ] `ayuda` y `semana` probados en Teams en los últimos minutos, no "la última vez que se probó".
- [ ] El `logging.basicConfig(level=logging.DEBUG)` temporal de `app/main.py`, si se agregó para
      diagnosticar algo, **no** está presente (o se sabe conscientemente que sí y por qué).

---

## 8. Referencias cruzadas

| Si necesitas... | Ve a... |
|---|---|
| Crear el tenant, registrar la app de Entra, registrar el bot, generar el paquete de Teams desde cero | `docs/RUNBOOK-TENANT.md` |
| Entender la arquitectura y qué hace el proyecto | `README.md` |
| Explicarle a un administrador de TI de un cliente cómo instalar Brújula en su organización | `docs/GUIA-INSTALACION-TI.md` |
| Ver el historial de decisiones y el estado de los riesgos | `docs/BITACORA.md` |

---

## 9. Producción: vigilancia precargada

El despliegue ejecuta dos procesos del mismo contenedor: `app` atiende Teams y `worker` actualiza
la bandeja de quienes activaron `vigilar`. Ambos deben recibir el mismo `.env` con:

```dotenv
AZURE_REDIRECT_URI=https://brujula-teams.duckdns.org/auth/callback
BRUJULA_URL_PUBLICA=https://brujula-teams.duckdns.org
BRUJULA_TOKEN_ENCRYPTION_KEY=<clave-Fernet-generada-una-sola-vez>
```

Genera la clave una sola vez en el servidor y guárdala únicamente en el `.env` de producción:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

En Entra, registra exactamente la misma URL de `AZURE_REDIRECT_URI` como plataforma **Web**. Luego
despliega ambos procesos con `docker compose up -d --force-recreate` y verifica que `docker compose
ps` muestre `app` y `worker` en ejecución.

Prueba final: escribe `vigilar`, completa Microsoft, espera hasta un minuto, escribe `revisar` y
verifica una sugerencia; después escribe `no vigilar` y confirma que una nueva revisión no se
actualiza. Nunca pegues la clave Fernet, el secreto de cliente ni tokens en el chat o repositorio.
