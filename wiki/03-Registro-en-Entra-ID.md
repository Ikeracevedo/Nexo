# 3 · Registro de la aplicación en Entra ID

⏱️ ~30 minutos · 🔑 Requiere rol de administrador

Aquí creas la identidad con la que Nexo **pide permiso** a cada usuario para leer sus datos. Es la primera de las dos identidades del sistema.

## 3.1 — Crear el registro

1. `entra.microsoft.com` → **Identity → Applications → App registrations → New registration**
2. Rellena:

| Campo | Valor |
|---|---|
| **Name** | `Nexo` |
| **Supported account types** | **Accounts in any organizational directory (Any Microsoft Entra ID tenant - Multitenant)** |
| **Redirect URI** | Plataforma **Web** → `https://TU-DOMINIO/auth/callback` |

3. **Register**

> **Por qué multiinquilino.** Un registro de un solo inquilino solo sirve para tu organización. Si eliges multiinquilino, el mismo despliegue puede atender a varias empresas y cada una consiente por su cuenta. Si Nexo es solo para ti, *Single tenant* también funciona — pero cambiarlo después obliga a rehacer el consentimiento de todos los usuarios.

4. Copia de la pantalla **Overview**:
   - **Application (client) ID** → es tu `AZURE_CLIENT_ID`
   - **Directory (tenant) ID** → es tu `AZURE_TENANT_ID`

> ⚠️ **Los dos son GUID de exactamente 36 caracteres.** Cópialos con el botón de copiar, nunca a mano. Un GUID al que le falta un carácter produce un error de autenticación opaco (`AADSTS900023`) que aparece mucho después y no menciona el dato mal copiado. Nexo valida el formato al arrancar precisamente por esto.

## 3.2 — Crear el secreto

1. **Certificates & secrets → Client secrets → New client secret**
2. Descripción: `nexo-produccion`. Caducidad: **24 meses** (el máximo).
3. **Copia la columna `Value` inmediatamente** → es tu `AZURE_CLIENT_SECRET`

> 🔴 **El valor solo se muestra una vez.** Si cierras la pantalla, no hay forma de recuperarlo: hay que crear otro. Y no copies el `Secret ID`, que es el identificador y no sirve para autenticar.

> 📅 **Apunta la fecha de caducidad en el calendario de tu equipo, con un aviso un mes antes.** El día que caduque, Nexo dejará de funcionar sin previo aviso y el error no dirá "el secreto caducó".

## 3.3 — Los permisos

**API permissions → Add a permission → Microsoft Graph → Delegated permissions**

Añade exactamente estos siete:

| Permiso | Para qué |
|---|---|
| `User.Read` | Identificar al usuario |
| `Calendars.Read` | Eventos del calendario |
| `Tasks.Read` | To Do **y** Planner |
| `Chat.ReadBasic` | Listar los chats |
| `Chat.Read` | Leer los mensajes de esos chats |
| `Group.Read.All` | Resolver los planes de Planner |
| `offline_access` | Renovar el acceso sin pedir login otra vez |

> Fíjate en la columna **"Admin consent required"** mientras los añades, y anótala. Te dice cuáles puede aceptar un usuario por su cuenta y cuáles necesitan al administrador. `Group.Read.All` lo requiere siempre.

4. **Grant admin consent for [tu organización]** → **Yes**

Las siete filas deben quedar con un check verde en *Status*. Si alguna sigue en blanco, el consentimiento no se aplicó y esa fuente devolverá `403`.

## 3.4 — Los dos Redirect URI

En **Authentication**, confirma que están los dos:

```
https://TU-DOMINIO/auth/callback          ← el login propio de Nexo
https://token.botframework.com/.auth/web/redirect   ← el login desde Teams
```

El segundo es de Microsoft y es el que usa Bot Framework cuando el usuario escribe `conectar` dentro de Teams. **Sin él, el botón de iniciar sesión falla con un error genérico de "la aplicación no existe"** que no apunta a la causa.

## ✅ Antes de pasar al siguiente paso

- [ ] Tengo el `AZURE_CLIENT_ID` (36 caracteres)
- [ ] Tengo el `AZURE_TENANT_ID` (36 caracteres)
- [ ] Tengo el `AZURE_CLIENT_SECRET` guardado **y verificado** (el `Value`, no el `Secret ID`)
- [ ] Los siete permisos con check verde
- [ ] Los dos Redirect URI
- [ ] La fecha de caducidad del secreto, en el calendario

Siguiente: [Azure Bot](04-Azure-Bot).
