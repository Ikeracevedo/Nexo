<div align="center">
  <img src="docs/logo-upb.png" alt="Universidad Pontificia Bolivariana" width="340"/>

  <h1> Nexo Teams </h1>

  <p><strong>Tus pendientes están regados entre Planner, To Do, el calendario y un mensaje perdido<br>
  en un canal de Teams. Nexo los reúne todos y te dice, de una vez, qué tienes esta semana.</strong></p>

  <p>
    <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white" />
    <img src="https://img.shields.io/badge/FastAPI-0.118-009688?logo=fastapi&logoColor=white" />
    <img src="https://img.shields.io/badge/Pydantic-2-E92063?logo=pydantic&logoColor=white" />
    <img src="https://img.shields.io/badge/Microsoft%20Teams-bot-6264A7?logo=microsoftteams&logoColor=white" />
    <img src="https://img.shields.io/badge/pytest-tested-0A9EDC?logo=pytest&logoColor=white" />
    <img src="https://img.shields.io/badge/mypy-strict-1F5582" />
    <img src="https://img.shields.io/badge/ruff-linted-D7FF64?logo=ruff&logoColor=black" />
  </p>

  <p><strong>Proyecto en TIC 1 — Ingeniería de Sistemas e Informática · Universidad Pontificia Bolivariana</strong></p>
</div>

---

## La idea

Un pendiente de la semana rara vez vive en un solo sitio: una tarea en Planner, un recordatorio en
To Do, una reunión en el calendario, y un "para el viernes necesito X" que alguien escribió en un
canal de Teams y que nadie vuelve a leer. Nexo pregunta una sola cosa — **¿qué tengo esta
semana?** — y reúne la respuesta de todas partes, con un detalle que la hace confiable: **nunca te
presenta una suposición como si fuera un hecho.** Lo que viene de un sistema real se muestra
confirmado; lo que Nexo cree entender de una conversación se marca aparte, con su nivel de
confianza, para que lo verifiques tú.

**Lo que vas a poder hacer:**

| | |
|---|---|
| 🗂️ **Ver todo junto** | Una sola lista con los pendientes de los próximos 7 días, sin abrir cuatro apps distintas. |
| 🔗 **Ir directo a la fuente** | Cada pendiente enlaza al lugar exacto de donde salió — Planner, To Do, el calendario o la conversación. |
| ✅ **Confiar en lo que es un hecho** | Lo que viene de un sistema estructurado se muestra como confirmado, sin ambigüedad. |
| 💡 **Ver lo que es una inferencia** | Lo que Nexo detecta en una conversación se marca aparte, con su nivel de confianza y un aviso para verificarlo. |
| 💬 **Preguntarle desde Teams** | Escribe `semana` o `ayuda` en un chat con Nexo, sin salir de donde ya trabajas. |
| 🚧 **Saber cuándo algo falló** | Si una fuente no responde, Nexo lo dice — nunca confunde un fallo con "no tienes nada pendiente". |

---

## Tecnologías

| Capa | Tecnología | Rol |
|---|---|---|
| Backend | Python 3.12 + FastAPI | Núcleo de la aplicación y canal REST |
| Configuración | Pydantic Settings | Variables de entorno validadas (nunca arranca con datos mal copiados) |
| Canal de Teams | `microsoft-teams-apps` (Microsoft 365 Agents SDK) | Bot conversacional, montado sobre la misma app FastAPI |
| Túnel de desarrollo | Microsoft `devtunnel` | Expone el backend local a Teams durante el desarrollo |
| Calidad | pytest · ruff · mypy (`--strict`) | Pruebas automatizadas, formato y tipado estricto |

---

## Arquitectura

Nexo es **un solo backend con dos puertas de entrada** que hacen la misma pregunta al mismo
motor interno — no hay una copia de la lógica por canal:

```
app/
├── dominio/       # Qué es un "pendiente", con sus reglas propias.
├── servicios/     # El motor: reúne pendientes de todas las fuentes conectadas.
├── adaptadores/   # Microsoft Graph, MongoDB y Gemini detrás de puertos.
├── api/           # Puerta 1 — REST: GET /api/agenda
├── bot/           # Puerta 2 — Teams: escribes "semana" y responde por ahí
└── main.py        # Arma la aplicación completa y conecta las dos puertas al mismo motor
```

Por eso agregar una fuente nueva (por ejemplo, Google Classroom) es escribir una pieza nueva, no
tocar el resto del sistema — y por eso el bot de Teams y el endpoint web nunca pueden dar
respuestas distintas a la misma pregunta.

---

## Instalación y arranque

Este README explica **qué es** Nexo y **qué vas a poder hacer con ella**. Para levantar el
proyecto paso a paso en tu máquina — el entorno, el túnel, el servidor, y qué hacer si algo deja de
responder — está **[`docs/GUIA-OPERACION.md`](docs/GUIA-OPERACION.md)**.

Arranque rápido si el entorno ya existe (detalle completo en esa guía):

```powershell
.venv\Scripts\Activate.ps1
devtunnel host brujula-dev          # en una terminal
uvicorn app.main:app --reload       # en otra terminal
```

---

## Estado actual y comandos

En Teams, `semana` reúne calendario, To Do, Planner y pendientes creados con
`recuérdame <texto>`. Las preguntas libres sobre la agenda consultan esas
fuentes y declaran cualquier fallo parcial. `conectar`, `desconectar`, `estado`
y `ayuda` gestionan la sesión y explican el estado.

El aporte de Julián agrega `chat <pregunta>` para conversación general con
memoria y lectura de imágenes pegadas en Teams. `olvidar` borra la memoria de
quien lo escribe en esa conversación. Este flujo está separado de la agenda:
una respuesta general de Gemini no se presenta como un pendiente confirmado.

El endpoint HTTP `/api/agenda` todavía usa la fuente de ejemplo. En Teams,
`vigilar` permite autorizar de forma explícita la lectura limitada de chats;
el worker detecta sugerencias y `revisar` las muestra para que el usuario las
acepte o descarte. La interfaz web responsive sigue pendiente.

---

## Equipo

| Integrante |
|---|
| Iker Acevedo | 
| Julián | 
| Antonio |

Ingeniería de Sistemas e Informática · Universidad Pontificia Bolivariana
Proyecto en TIC 1
