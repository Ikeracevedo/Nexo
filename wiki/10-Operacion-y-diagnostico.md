# 10 · Operación y diagnóstico

## Comandos del día a día

```bash
docker compose ps                      # estado
docker compose logs -f app             # logs del bot
docker compose logs -f worker          # logs de la precarga
docker compose pull && docker compose up -d --force-recreate   # actualizar
docker compose restart app             # reiniciar sin actualizar
curl https://tu-dominio.com/health     # salud
```

> Siempre `--force-recreate` cuando toques el `.env`. Siempre.

## Mantenimiento programado

| Cuándo | Qué |
|---|---|
| **Semanal** | Mirar los logs en busca de errores repetidos |
| **Mensual** | Uso del clúster de Atlas (M0 son 512 MB) y consumo de Gemini |
| **Cada 3 meses** | `docker compose pull` para traer la última imagen |
| **🔴 Antes de los 24 meses** | **Renovar el `AZURE_CLIENT_SECRET`** — ver abajo |

### El secreto que caduca

Es la avería programada de este sistema. El día que caduque, Nexo dejará de poder leer datos y **el error no dirá "el secreto caducó"**.

Pon un recordatorio **un mes antes** de la fecha que anotaste en el paso 3.2. Renovar es: crear un secreto nuevo en Entra ID → actualizarlo en el `.env` **y en la conexión OAuth del Azure Bot** → `docker compose up -d --force-recreate`.

> Son dos sitios, no uno. Olvidar el segundo deja `conectar` roto mientras el resto parece ir bien.

## Tabla de síntomas

| Síntoma | Causa más probable | Solución |
|---|---|---|
| El bot no responde nada | Messaging endpoint mal, o canal de Teams sin activar | Paso 4.3 y 4.4 |
| `/health` no responde desde fuera | Firewall, DNS o Caddy | Paso 7.2 y 7.3 |
| *"App does not exist"* al conectar | Falta `token.botframework.com` en `validDomains` | Paso 8.2 |
| Responde, pero `semana` no trae datos | El usuario no ha escrito `conectar` | Que lo escriba |
| Una fuente dice "requiere autorización" | Permiso ausente, o token emitido antes de añadirlo | `desconectar` + `conectar` |
| Todas las fuentes fallan a la vez | Secreto caducado o mal copiado | Paso 3.2 |
| Planner vacío, el resto bien | **Normal** si no hay planes en grupos de M365 | Crear un plan de prueba |
| Mongo no responde | IP fuera de Network Access, o contraseña con símbolos | Paso 5.3 y 5.2 |
| *"No pude generar una respuesta"* | Sin `GEMINI_API_KEY` o cuota agotada | Paso 6 |
| Cambié el `.env` y no pasó nada | Falta `--force-recreate` | `docker compose up -d --force-recreate` |
| Fechas con horas raras | `BRUJULA_ZONA_HORARIA` mal puesta | Zona IANA, p.ej. `America/Bogota` |
| El contenedor no arranca en producción | Falta `TEAMS_BOT_ID` — **es deliberado** | Rellenar la variable |

## Leer los logs

```bash
docker compose logs app | grep -i "error\|warning" | tail -50
docker compose logs app | grep "FuenteNoDisponible"   # qué fuente falla y por qué
docker compose logs worker | tail -30                  # última pasada de precarga
```

Los mensajes están pensados para leerse: cuando una fuente falla, el log dice **cuál** y **con qué código**, no un *stack trace* genérico.

## Copias de seguridad

| Qué | Cómo | Cada cuánto |
|---|---|---|
| Base de datos | Atlas → **Backup** (en M0, `mongodump`) | Semanal |
| `.env` | Gestor de secretos de la empresa | Al cambiarlo |
| `BRUJULA_TOKEN_ENCRYPTION_KEY` | 🔴 Gestor de secretos | **Ahora** |
| Paquete de Teams | En tu repositorio | Al cambiarlo |

> Si pierdes la clave de cifrado, los tokens guardados quedan ilegibles y todos los usuarios tendrán que escribir `conectar` otra vez. Recuperable, pero visible para toda la organización.

## Desinstalar

1. Teams admin center → **Manage apps** → Nexo → **Block/Delete**
2. `docker compose down`
3. Borrar la base de datos en Atlas (**esto borra los pendientes propios de todos**)
4. Eliminar el registro de Entra ID y el Azure Bot

> Cada usuario puede revocar su parte por su cuenta, sin desinstalar nada, escribiendo `desconectar`.

Siguiente: [Privacidad y cumplimiento](11-Privacidad-y-cumplimiento).
