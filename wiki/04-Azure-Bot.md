# 4 · Azure Bot

⏱️ ~20 minutos

Esta es la **segunda identidad**. El registro de Entra ID sirve para leer los datos del usuario; el Azure Bot sirve para que **Teams sepa a qué servidor entregar los mensajes**. Son cosas distintas y no se pueden mezclar.

## 4.1 — Crear el recurso

1. `portal.azure.com` → **Create a resource** → busca **Azure Bot** → **Create**

| Campo | Valor |
|---|---|
| **Bot handle** | `nexo-bot` (único en todo Azure; si está tomado, añade un sufijo) |
| **Subscription / Resource group** | Los tuyos |
| **Pricing tier** | **F0 (Free)** — suficiente de sobra |
| **Type of App** | **Multi Tenant** (el mismo criterio del paso 3) |
| **Creation type** | **Create new Microsoft App ID** |

2. **Review + create → Create**

## 4.2 — Las credenciales del bot

En el recurso creado, **Configuration**:

- **Microsoft App ID** → es tu `TEAMS_BOT_ID`
- **Manage** (al lado del App ID) → te lleva al registro de la app del bot → **Certificates & secrets → New client secret** → copia el `Value` → es tu `TEAMS_BOT_PASSWORD`

> 🔴 Otra vez: **el valor solo se ve una vez**. Y ojo — este secreto es de la app **del bot**, no del registro que creaste en el paso 3. Son dos apps distintas con dos secretos distintos.

## 4.3 — El Messaging endpoint

En **Configuration → Messaging endpoint**:

```
https://TU-DOMINIO/api/messages
```

Si todavía no tienes el dominio, déjalo vacío y vuelve aquí en el paso 7. **No pongas `http://`**: Bot Framework lo rechaza.

## 4.4 — Activar el canal de Teams

**Channels → Microsoft Teams → Accept → Apply**

Sin esto, el bot existe pero Teams no puede hablar con él.

## 4.5 — La conexión OAuth

Esto es lo que permite el botón de *"Iniciar sesión"* dentro de la conversación de Teams.

**Configuration → Add OAuth Connection Settings → Add OAuth Connection Settings**

| Campo | Valor |
|---|---|
| **Name** | `graph` ⚠️ exactamente así, en minúsculas |
| **Service Provider** | **Azure Active Directory v2** |
| **Client id** | Tu `AZURE_CLIENT_ID` — ⚠️ **el del paso 3**, no el del bot |
| **Client secret** | Tu `AZURE_CLIENT_SECRET` — también el del paso 3 |
| **Token Exchange URL** | *(vacío)* |
| **Tenant ID** | `common` |
| **Scopes** | `openid profile offline_access User.Read Calendars.Read Tasks.Read Chat.Read Chat.ReadBasic Group.Read.All` |

> **Éste es el punto donde la gente confunde las dos identidades**, y el síntoma es cruel: el bot responde a `ayuda` perfectamente, pero `conectar` falla o `semana` devuelve `403`. Si eso te pasa, vuelve aquí y comprueba que el *Client id* es el del registro de Entra ID del paso 3.
>
> Si cambias el nombre `graph`, tendrás que ajustar la variable `TEAMS_OAUTH_CONNECTION` en el paso 7.

### Probar la conexión sin desplegar nada

Pulsa **Test Connection** en la conexión que acabas de crear. Debe abrir el login de Microsoft y terminar mostrándote un token.

**Hazlo ahora.** Es el único momento en que puedes verificar el OAuth sin tener el servidor levantado — y si falla aquí, el problema está en el portal, no en tu infraestructura. Diagnosticar eso más tarde, con el contenedor en marcha, cuesta cinco veces más.

## ✅ Antes de pasar al siguiente paso

- [ ] `TEAMS_BOT_ID` anotado
- [ ] `TEAMS_BOT_PASSWORD` anotado **y verificado**
- [ ] Canal de Teams activado
- [ ] Conexión OAuth llamada `graph`, con el client id **del paso 3**
- [ ] **Test Connection devuelve un token** ⭐

Siguiente: [MongoDB Atlas](05-MongoDB-Atlas).
