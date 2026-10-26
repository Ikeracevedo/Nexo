# 2 · Requisitos previos

Reúne esto antes de empezar. Si te falta algo a mitad del paso 3, vas a tener que deshacer trabajo.

## Cuentas y licencias

| Necesitas | Detalle | Cómo comprobarlo |
|---|---|---|
| **Tenant de Microsoft 365** | Con Teams activo | Entra en `teams.microsoft.com` con una cuenta de la empresa |
| **Rol de administrador** | *Global Administrator* o *Application Administrator* | `entra.microsoft.com` → Identity → Roles and administrators → tu usuario |
| **Suscripción de Azure** | Aunque sea la gratuita o la de estudiante | `portal.azure.com` → Subscriptions |
| **Permiso para subir apps a Teams** | Muchos tenants lo tienen **desactivado** | Ver abajo ⚠️ |
| **Cuenta de Google** | Para la clave de Gemini | Cualquiera |
| **Cuenta de MongoDB Atlas** | La capa gratuita basta para empezar | `cloud.mongodb.com` |

### ⚠️ Comprueba esto HOY, antes que nada

**Si tu organización no permite aplicaciones personalizadas en Teams, no se puede instalar Nexo**, y cambiar esa política puede tardar días en aprobarse internamente.

1. Entra en `admin.teams.microsoft.com`
2. **Teams apps → Setup policies → Global**
3. Mira **"Upload custom apps"**

Si está en *Off*, habrá que activarlo (o crear una política para un grupo piloto). **Es el único requisito que puede bloquear el proyecto durante una semana entera**, así que compruébalo antes de invertir tres horas.

> La propagación de un cambio de política de Teams puede tardar **hasta 24 horas**. Actívalo hoy aunque vayas a instalar la semana que viene.

## Infraestructura

Nexo necesita un servidor con **HTTPS válido y accesible desde internet**.

> **HTTPS no es opcional.** Bot Framework **rechaza** los endpoints en HTTP plano: no es una recomendación de seguridad, es un requisito técnico que hará que nada funcione.

| Opción | Coste aproximado | Cuándo elegirla |
|---|---|---|
| **VM pequeña** (Azure B2s, EC2 t3.small, Droplet) | 12–20 USD/mes | Control total. Es la que documenta esta guía |
| **Azure Container Apps / Cloud Run** | Variable, con capa gratuita | Si no quieres administrar un servidor |
| **Cualquier host con Docker y dominio** | — | Si ya tienes infraestructura |

Mínimos: **2 vCPU, 2 GB de RAM, 20 GB de disco**, Linux con Docker y Docker Compose.

Y un **nombre de dominio**. Si no tienes uno, un subdominio gratuito de DuckDNS sirve perfectamente para empezar.

## Costes reales

| Componente | Capa gratuita | Si creces |
|---|---|---|
| Entra ID + Azure Bot (F0) | Gratis | Gratis |
| MongoDB Atlas M0 | Gratis, 512 MB | M10 desde ~57 USD/mes |
| Gemini 2.5 Flash | Cuota gratuita generosa | Por tokens, céntimos al día |
| VM | — | 12–20 USD/mes |
| **Total para un piloto** | **~15 USD/mes** | |

> **Las APIs de Teams dejaron de estar medidas el 25 de agosto de 2025.** Leer mensajes de chats y canales ya **no requiere modelo de pago ni configuración de facturación**. Si encuentras documentación o tutoriales que hablan de "modelo A o B" y capacidad sembrada, están desactualizados.

## Lo que vas a ir anotando

Abre un documento y ten a mano estos ocho valores. Los irás rellenando y los necesitarás todos juntos en el paso 7:

```
AZURE_TENANT_ID        = ...   (paso 3)
AZURE_CLIENT_ID        = ...   (paso 3)
AZURE_CLIENT_SECRET    = ...   (paso 3)  ⚠️ solo se ve UNA vez
TEAMS_BOT_ID           = ...   (paso 4)
TEAMS_BOT_PASSWORD     = ...   (paso 4)  ⚠️ solo se ve UNA vez
MONGODB_URI            = ...   (paso 5)
GEMINI_API_KEY         = ...   (paso 6)
BRUJULA_URL_PUBLICA    = ...   (paso 7)
```

> **Guárdalos en el gestor de secretos de tu empresa, no en un bloc de notas.** Dos de ellos son contraseñas que solo se muestran una vez; si los pierdes, hay que regenerarlos.

Siguiente: [Registro en Entra ID](03-Registro-en-Entra-ID).
