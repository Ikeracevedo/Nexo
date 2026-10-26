# 5 · MongoDB Atlas

⏱️ ~20 minutos

Aquí viven los pendientes propios, las sugerencias, las preferencias de cada usuario y los *refresh tokens* cifrados.

## 5.1 — Crear el clúster

1. `cloud.mongodb.com` → crea una organización y un proyecto (`Nexo`)
2. **Create a deployment → M0 (Free)**
3. **Elige la región más cercana a tu servidor**, y anótala

> La región no es un detalle técnico: es **dónde residen físicamente los datos de tus usuarios**. Si tu organización tiene requisitos de residencia de datos, ésta es la decisión que los cumple o los incumple. Anótala, porque un administrador de TI te la va a preguntar.

## 5.2 — Usuario de base de datos

**Database Access → Add New Database User**

- Autenticación: **Password**
- Usuario: `nexo-app`
- Contraseña: **genera una larga y sin caracteres especiales raros** (ver aviso abajo)
- Permisos: **Read and write to any database**

> ⚠️ **La contraseña va dentro de una URL.** Si contiene `@`, `:`, `/` o `#`, rompe la cadena de conexión de formas confusas. Usa el botón *Autogenerate* de Atlas, o quédate en letras y números. Si ya tienes una con símbolos, hay que codificarla en *percent-encoding* — más fácil cambiarla.

## 5.3 — Acceso de red

**Network Access → Add IP Address**

| Opción | Cuándo |
|---|---|
| **La IP pública de tu servidor** | ✅ Recomendado en producción |
| `0.0.0.0/0` (desde cualquier sitio) | Solo para probar, y quítalo después |

> Por defecto Atlas **bloquea todo**, y el síntoma de no haber hecho este paso es un *timeout* genérico que parece un fallo de tu código. Es una de las dos causas más frecuentes de "Mongo no responde" en la primera instalación.

## 5.4 — La cadena de conexión

**Database → Connect → Drivers → Python**

```
mongodb+srv://nexo-app:TU-CONTRASEÑA@cluster0.xxxxx.mongodb.net/nexo?retryWrites=true&w=majority
```

- Sustituye `TU-CONTRASEÑA` por la real
- **Añade `/nexo`** antes del `?` — es el nombre de la base de datos
- Esto es tu `MONGODB_URI`

## 5.5 — Índices

No son obligatorios para arrancar, pero con unos pocos miles de documentos la diferencia se nota. En **Collections → Indexes**, o desde `mongosh`:

```javascript
db.pendientes.createIndex({ usuario_id: 1, completado: 1, vence: 1 })
db.sugerencias.createIndex({ usuario_id: 1, estado: 1 })
db.preferencias.createIndex({ usuario_id: 1 }, { unique: true })
db.estados_oauth.createIndex({ creado_en: 1 }, { expireAfterSeconds: 600 })
```

> El último es un **índice TTL**: hace que MongoDB borre solo los estados de login a los 10 minutos. Es higiene de seguridad gratis — un estado OAuth caducado que se queda en la base es superficie de ataque sin ninguna utilidad.

## ✅ Antes de pasar al siguiente paso

- [ ] Clúster creado, región anotada
- [ ] Usuario `nexo-app` con contraseña sin símbolos problemáticos
- [ ] IP del servidor permitida en Network Access
- [ ] `MONGODB_URI` completa, **con `/nexo`** incluido

Siguiente: [Google Gemini](06-Google-Gemini).
