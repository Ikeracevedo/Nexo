# 7 · Servidor y despliegue

⏱️ ~40 minutos

Aquí se junta todo. Al terminar, Nexo estará corriendo con HTTPS y accesible desde internet.

## 7.1 — El servidor

Cualquier Linux con Docker. Mínimos: 2 vCPU, 2 GB RAM, 20 GB disco. Abre los puertos **80** y **443**; el 8000 queda detrás del proxy, sin exponer.

```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker
docker --version && docker compose version
```

## 7.2 — El dominio

Necesitas un nombre que apunte a la IP pública del servidor.

**Con dominio propio:** crea un registro `A` → la IP.

**Sin dominio:** `duckdns.org` da un subdominio gratis. Crea `tu-empresa-nexo.duckdns.org` y apúntalo a la IP.

```bash
nslookup tu-dominio    # debe devolver la IP del servidor
```

> La propagación del DNS puede tardar. Si no resuelve, **espera antes de seguir**: el certificado no se puede emitir contra un nombre que todavía no apunta a ningún sitio, y vas a perder media hora diagnosticando el problema equivocado.

## 7.3 — HTTPS con Caddy

Caddy obtiene y renueva el certificado de Let's Encrypt solo. `Caddyfile`:

```
tu-dominio.com {
    reverse_proxy localhost:8000
}
```

```bash
sudo apt install -y debian-keyring debian-archive-keyring apt-transport-https
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' \
  | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' \
  | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt update && sudo apt install caddy
sudo systemctl reload caddy
```

Comprueba desde **otra red** (el móvil con datos, no el wifi de la oficina):

```bash
curl -I https://tu-dominio.com
```

## 7.4 — La clave de cifrado

Nexo cifra los *refresh tokens* antes de guardarlos. Genera la clave **en el servidor**, una sola vez:

```bash
docker run --rm python:3.12-slim sh -c \
  "pip install -q cryptography && python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
```

> 🔴 **Guárdala en el gestor de secretos de tu empresa y nunca en el repositorio.** Si la pierdes, los tokens guardados quedan ilegibles y **todos los usuarios tendrán que escribir `conectar` otra vez**. No es catastrófico, pero es una interrupción visible para todo el mundo.

## 7.5 — El archivo `.env`

En el servidor, junto al `docker-compose.yml`:

```bash
BRUJULA_ENTORNO=produccion
BRUJULA_LOG_LEVEL=INFO
BRUJULA_ZONA_HORARIA=America/Bogota
BOT_NOMBRE=Nexo

# Paso 3 — registro de Entra ID
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
AZURE_REDIRECT_URI=https://tu-dominio.com/auth/callback

# Paso 4 — Azure Bot (identidad DISTINTA)
TEAMS_BOT_ID=
TEAMS_BOT_PASSWORD=
TEAMS_OAUTH_CONNECTION=graph

# Paso 5
MONGODB_URI=

# Paso 6
GEMINI_API_KEY=
GEMINI_MODELO=gemini-2.5-flash

# Paso 7
BRUJULA_URL_PUBLICA=https://tu-dominio.com
BRUJULA_TOKEN_ENCRYPTION_KEY=
```

```bash
chmod 600 .env
```

> **`BRUJULA_ENTORNO=produccion` no es cosmético.** Fuera de `local`, si falta `TEAMS_BOT_ID` la aplicación **se niega a arrancar**. Es deliberado: sin esa credencial el endpoint `/api/messages` aceptaría mensajes sin autenticar, y un secreto ausente debe **cerrar** la puerta, no abrirla. Un fallo de arranque se ve en los logs en dos segundos; un endpoint abierto no se ve nunca.
>
> **`BRUJULA_URL_PUBLICA` va sin barra final y sin `/docs`.**

## 7.6 — Levantarlo

`docker-compose.yml`:

```yaml
services:
  app:
    image: ghcr.io/ikeracevedo/brujula-teams:latest
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
  worker:
    image: ghcr.io/ikeracevedo/brujula-teams:latest
    restart: unless-stopped
    command: ["python", "-m", "app.worker"]
    env_file:
      - .env
    healthcheck:
      disable: true
```

```bash
docker compose pull
docker compose up -d --force-recreate
docker compose logs -f
```

> 🔴 **`--force-recreate` no es opcional.** `docker compose up -d` **no recrea el contenedor cuando cambia el `.env`**: lee la imagen, ve que no cambió y deja el contenedor viejo con las variables viejas. Es el error que más tiempo cuesta en cada actualización, porque todo *parece* haber funcionado.

### Por qué hay dos servicios

| Servicio | Qué hace |
|---|---|
| **app** | Atiende Teams y la API. Tiene que responder en segundos. |
| **worker** | Refresca los datos de cada usuario en segundo plano, una pasada por minuto. |

Si la precarga viviera dentro del bot, cada `semana` esperaría a cuatro llamadas a Microsoft Graph y Teams daría sensación de lentitud. **Separarlos es lo que hace que la respuesta sea inmediata.**

## 7.7 — Cerrar el círculo en Azure

Vuelve al portal y pon la URL real donde faltaba:

1. **Azure Bot → Configuration → Messaging endpoint** → `https://tu-dominio.com/api/messages`
2. **Entra ID → Authentication → Redirect URI** → que esté `https://tu-dominio.com/auth/callback`

```bash
curl https://tu-dominio.com/health
# {"estado":"ok","version":"...","entorno":"produccion"}
```

## ✅ Antes de pasar al siguiente paso

- [ ] `https://tu-dominio.com/health` responde 200 **desde fuera de tu red**
- [ ] Los dos contenedores en `Up` (`docker compose ps`)
- [ ] Messaging endpoint y Redirect URI actualizados con el dominio real
- [ ] `.env` con permisos `600` y respaldado en el gestor de secretos

Siguiente: [Paquete de Teams](08-Paquete-de-Teams).
