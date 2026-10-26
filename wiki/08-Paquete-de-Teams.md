# 8 · El paquete de Teams

⏱️ ~15 minutos

Un `.zip` con tres archivos que le dice a Teams cómo se llama el bot, qué icono tiene y con qué identidad hablar.

## 8.1 — Los tres archivos

```
appPackage/
├── manifest.json
├── color.png      192 × 192 px, con fondo
└── outline.png    32 × 32 px, blanco sobre transparente
```

## 8.2 — El manifiesto

Parte del que viene en `teams/nexo/appPackage/manifest.json` del repositorio y cambia lo marcado:

```jsonc
{
  "$schema": "https://developer.microsoft.com/en-us/json-schemas/teams/v1.17/MicrosoftTeams.schema.json",
  "manifestVersion": "1.17",
  "version": "1.0.0",
  "id": "GENERA-UN-GUID-NUEVO",          // ⚠️ distinto del bot y de la app de Entra
  "developer": {
    "name": "TU EMPRESA",
    "websiteUrl": "https://tu-empresa.com",
    "privacyUrl": "https://tu-empresa.com/privacidad",
    "termsOfUseUrl": "https://tu-empresa.com/terminos"
  },
  "name":        { "short": "Nexo", "full": "Nexo, tu asistente en Teams" },
  "description": {
    "short": "Reúne tus pendientes de Microsoft 365 en un solo sitio.",
    "full":  "Nexo unifica tus eventos de calendario, tareas de To Do y Planner y los compromisos que adquieres en tus conversaciones, y te los muestra en una sola respuesta con enlace a su origen."
  },
  "icons": { "color": "color.png", "outline": "outline.png" },
  "accentColor": "#2A6DF4",
  "bots": [{
    "botId": "TU-TEAMS-BOT-ID",          // ⚠️ el del paso 4
    "scopes": ["personal"],
    "supportsFiles": true,
    "isNotificationOnly": false
  }],
  "permissions": ["identity", "messageTeamMembers"],
  "validDomains": ["token.botframework.com", "tu-dominio.com"]
}
```

### Los tres puntos donde falla

1. **`id` es un GUID nuevo**, de la aplicación de Teams. **No es el `botId` ni el `AZURE_CLIENT_ID`.** Genera uno (`uuidgen`, o cualquier generador online).
2. **`token.botframework.com` tiene que estar en `validDomains`.** Si falta, `conectar` falla con *"App does not exist"* — un mensaje que no tiene nada que ver con la causa real.
3. **Las URLs de privacidad y términos deben existir y responder.** Teams las valida al subir el paquete y rechaza el `.zip` si dan 404.

## 8.3 — Empaquetar

Comprime **el contenido** de la carpeta, no la carpeta:

```bash
cd appPackage && zip -r ../nexo.zip manifest.json color.png outline.png
```

> Si al abrir el `.zip` ves una carpeta en vez de los tres archivos, Teams lo rechazará sin explicar por qué.

## 8.4 — Instalar

### Para probar tú solo

Teams → **Apps → Manage your apps → Upload an app → Upload a custom app** → el `.zip`

### Para toda la organización

1. `admin.teams.microsoft.com` → **Teams apps → Manage apps → Upload new app**
2. Sube el `.zip`
3. **Teams apps → Setup policies** → añade Nexo a la política (Global, o una de piloto)

> **Empieza por un grupo piloto de 5 a 10 personas**, no por toda la empresa. La propagación de políticas puede tardar **hasta 24 horas**, y con un piloto descubres los problemas reales (permisos, zonas horarias, nombres de chats) con gente que sabe que está probando.

## ✅ Antes de pasar al siguiente paso

- [ ] `id` del manifiesto es un GUID nuevo y propio
- [ ] `botId` es el `TEAMS_BOT_ID` del paso 4
- [ ] `validDomains` incluye `token.botframework.com`
- [ ] Las URLs de privacidad y términos responden 200
- [ ] El `.zip` contiene los tres archivos en la raíz
- [ ] Nexo aparece en Teams

Siguiente: [Verificación](09-Verificacion).
