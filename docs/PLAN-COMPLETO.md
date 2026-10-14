# PLAN MAESTRO — Asistente IA de Tareas para Microsoft Teams

> **Este documento es la fuente de verdad del proyecto.**
> Al abrir cualquier chat nuevo, leer este archivo primero, luego `BITACORA.md`.
> Versión 1.0 — 15 de agosto de 2026

---

## 0. Cómo se usa este documento

**Iker es el tech lead.** Claude actúa como mentor senior: da órdenes de trabajo, revisa entregas y verifica aprendizaje con preguntas. Iker ejecuta y reporta.

**Ciclo de trabajo:**

1. Claude asigna una **Orden de Trabajo (OT)** con criterio de aceptación explícito.
2. Iker la ejecuta en un chat nuevo dedicado.
3. Iker reporta el resultado.
4. Claude verifica con **preguntas de comprensión** (no basta con que funcione: hay que entender por qué).
5. Se registra en `BITACORA.md` y se libera la siguiente OT.

**Prompt para arrancar cualquier chat nuevo:**

```
Lee PLAN-MAESTRO.md y BITACORA.md en la carpeta del proyecto.
Vengo a ejecutar la OT-XX. Actúa como mi mentor senior según el plan.
```

---

## 1. El Norte del proyecto

> **Un agente conversacional dentro de Microsoft Teams que responde "¿qué tengo esta semana?"
> unificando pendientes dispersos en Planner, To Do, Calendario y mensajes de canal —
> entregando un resumen accionable con enlace a la fuente exacta.**

### Lo que SÍ es

- Agregador de pendientes multi-fuente con capa de normalización propia.
- Resumen generado por LLM, breve y bajo demanda ("abrebocas", no muro de texto).
- **Trazabilidad obligatoria**: toda afirmación del bot enlaza a su origen en Teams.
- Alcance de datos: **solo el usuario autenticado**, vía autenticación delegada.

### Lo que NO es (defender esta lista en sustentación)

- ❌ No es un chatbot de propósito general. Si preguntan por recetas de cocina, no responde.
- ❌ No lee la organización entera. Solo lo que el usuario ya puede ver.
- ❌ No resuelve las tareas. Orienta, contextualiza y enlaza.
- ❌ No reemplaza a Planner. Lo unifica con lo que Planner no ve.

### Objetivos personales de Iker (igual de importantes que la nota)

1. Aprender IA aplicada de verdad: RAG, embeddings, agentes, evaluación.
2. Repositorio público de calidad profesional, documentado, para portafolio.
3. Ejercer liderazgo técnico real sobre un equipo poco motivado.

---

## 2. Decisiones de Arquitectura (ADR)

> **ADR** = *Architecture Decision Record*. Cada decisión importante se registra con su
> contexto, la opción elegida y —lo más valioso— **lo que se descartó y por qué**.
> Cuando el profesor pregunte "¿por qué hiciste X?", la respuesta ya está escrita.

### ADR-001 — Backend en Python + FastAPI

**Decidido:** Python 3.11+ con FastAPI.

**Descartado:** .NET 8 + Semantic Kernel, pese a que Iker es desarrollador .NET.

**Razón:**
1. Python es la lengua franca del ecosistema de IA; maximiza tutoriales, librerías y valor de portafolio para roles de IA.
2. Coherente con la propuesta ya presentada al docente.
3. **Bus factor del equipo:** Julián y Antonio conocen Python y no conocen .NET. Elegir .NET habría concentrado el 100% del código en una sola persona y anulado cualquier posibilidad de delegar. La capacidad del equipo es un criterio de arquitectura legítimo, no una concesión.

> **Bus factor**: cuántas personas del equipo tendrían que desaparecer para que el proyecto se detenga. Un bus factor de 1 es un riesgo, no un logro.

**Costo aceptado conscientemente:** el soporte de Microsoft para bots de Teams es más maduro en C#. Habrá más fricción en la capa de bot.

**Mitigación obligatoria — Capa de Bot Delgada:**
La integración con Teams se aísla en un único módulo adaptador. El bot **solo** traduce mensajes entrantes a llamadas HTTP contra el núcleo y formatea la respuesta. Cero lógica de negocio en la capa de bot. Si el SDK pelea, se reemplaza por webhooks o por el frontend Angular sin tocar el núcleo.

**Disciplina compensatoria:** Iker viene de un lenguaje tipado. Se usará *type hinting* estricto + Pydantic + `mypy` desde el día 1. No es opcional: es lo que evita que un dev .NET escriba Python frágil.

---

### ADR-002 — Autenticación delegada, nunca permisos de aplicación

**Decidido:** OAuth 2.0 *on-behalf-of*. La app actúa **como el usuario**, con su token.

**Descartado:** permisos de aplicación (`ChannelMessage.Read.All`, `Files.Read.All`).

**Razón:**
- Los permisos de aplicación sobre mensajes de Teams son **Protected APIs**: requieren un formulario de solicitud a Microsoft con revisión semanal. No se aprueban para proyectos estudiantiles.
- Requieren consentimiento del administrador del tenant. Ninguna universidad lo otorga a una app de estudiantes.
- **Principio de mínimo privilegio** (OWASP): la app no debe poder hacer nada que el usuario no pueda.

**Consecuencia de diseño:** cero credenciales de usuario almacenadas. Solo tokens de corta vida y *refresh tokens* cifrados.

**Escape adicional documentado:** RSC (*Resource-Specific Consent*) permite que el dueño de un equipo específico autorice la app sobre ese equipo, sin tocar al admin del tenant. Es la vía si más adelante se necesita leer un canal completo.

---

### ADR-003 — Desarrollo sobre tenant propio, no sobre el de la universidad

**Decidido:** crear un tenant Microsoft 365 propio y desarrollar ahí desde el día 1.

**Descartado:** desarrollar contra el tenant de la UPB.

**Razón:** el tenant universitario probablemente bloquea la carga de apps personalizadas, y depender de aprobaciones de TI mata cronogramas. Además, **ningún proveedor de software serio desarrolla contra el tenant productivo de un cliente.**

**Beneficio estratégico:** reposiciona el proyecto como **producto ISV multi-tenant**. El entregable incluye una *Guía de Instalación para el Administrador de TI del cliente*. Eso convierte un trabajo de clase en un producto.

**Requisito:** cuenta *work/school* en un tenant. Las cuentas de consumidor (@outlook.com, @hotmail) **no sirven**: no tienen Teams empresarial, ni Planner, ni superficie útil de Graph.

---

### ADR-004 — Monolito modular con arquitectura hexagonal

**Decidido:** un solo desplegable, organizado en capas con dependencias hacia adentro.

**Descartado:** microservicios (sobre-ingeniería para 3 personas y un semestre — **YAGNI**).

**Regla de oro:** el núcleo de negocio **no sabe** que existen FastAPI, Mongo, Teams ni OpenAI. Solo conoce interfaces propias.

```
app/
├── domain/       # Entidades puras. Sin imports de librerías externas.
│   └── pendiente.py
├── ports/        # Interfaces (contratos): LLMProvider, TaskSource, VectorStore
├── services/     # Casos de uso. Orquestan el dominio. Testeables sin red.
├── adapters/     # Implementaciones: GraphPlannerSource, OpenAIProvider, MongoStore
└── api/          # FastAPI. Capa más externa y más delgada.
```

**Por qué importa:** permite testear toda la lógica con dobles de prueba, sin llamar a Microsoft ni gastar tokens. Y permite cambiar de LLM con una variable de entorno.

---

### ADR-005 — Modelo de dominio propio: `Pendiente`

**Decidido:** normalizar todas las fuentes a una entidad propia.

```python
@dataclass(frozen=True)
class Pendiente:
    id: str
    titulo: str
    fuente: FuentePendiente      # PLANNER | TODO | CALENDARIO | MENSAJE
    vence: datetime | None
    url_origen: str              # trazabilidad OBLIGATORIA
    confianza: float             # 1.0 si es estructurado; <1.0 si lo infirió el LLM
    contexto: str | None
```

**Razón:** los objetos crudos de Graph acoplan el sistema a Microsoft para siempre. Con este modelo, soportar Google Classroom mañana es escribir **un adaptador nuevo**, no reescribir el sistema.

El campo `confianza` es clave: distingue un hecho verificado (Planner) de una inferencia del LLM (un mensaje que *parece* asignar una tarea). Es honestidad de diseño y es la respuesta a la pregunta "¿y si alucina una fecha de entrega?".

---

### ADR-006 — Proveedor de LLM intercambiable

**Decidido:** interfaz `LLMProvider` con implementaciones intercambiables por configuración.

**Razón:** Azure OpenAI puede requerir solicitud de acceso o cuenta empresarial. No se puede hipotecar el proyecto a un proveedor incierto. Aplicación directa de **Inversión de Dependencias** (la D de SOLID).

**Consecuencia para QA:** existe un `FakeLLMProvider` determinista. Los tests corren sin red, sin costo y sin resultados aleatorios.

---

### ADR-007 — MongoDB Atlas como almacén único

**Decidido:** MongoDB Atlas para documentos, vectores e historial.

**Razón:** Atlas incluye **Vector Search** nativo. Elimina la necesidad de una base vectorial aparte (Pinecone, Qdrant): una dependencia menos, un despliegue menos, una cuenta menos.

---

### ADR-008 — Generación progresiva de respuestas

**Decidido:** respuesta en dos niveles — lista breve inmediata, detalle solo bajo demanda.

**Razón (corregida respecto a la intuición inicial):** el limitante **no es el cómputo** —resumir 20 tareas cuesta centavos—. Los limitantes reales son:

1. **Latencia**: nadie espera 15 segundos por un mensaje en Teams.
2. **UX**: un muro de texto no se lee.
3. **Economía de tokens**: importa a escala, no en el MVP.

**Implementación:** modelo rápido y barato para la lista; modelo mayor solo si el usuario pide profundizar en un ítem concreto.

---

### ADR-009 — Teams como canal primario; riesgo de rúbrica aceptado

**Decidido (2-sep-2026, por el tech lead):** Microsoft Teams es el canal principal y se construye
primero. El frontend web responsive se implementa en F4 como segundo canal.

**Descartado:** invertir la prioridad y hacer la web primero para blindar la nota.

**Riesgo aceptado conscientemente:** la rúbrica exige *"implementación responsive (Desk y Mobile)"*.
Un bot de Teams satisface el espíritu (Teams tiene cliente de escritorio y móvil) pero no de forma
literal e inequívoca. Si en F4 no alcanza el tiempo para el frontend web, la nota depende de la
interpretación del docente.

**Mitigación:**
1. El núcleo es agnóstico del canal (ADR-001, ADR-004). El frontend web consume la **misma** API
   sin tocar el dominio. Construirlo es trabajo de UI, no de arquitectura.
2. **Punto de reevaluación obligatorio: checkpoint del 30 de septiembre.** Si en esa fecha no hay
   un núcleo funcionando end-to-end, se congela Teams y se prioriza la web responsive.
   *No es una sugerencia: es un disparador con fecha.*
3. Consultar al docente si un bot de Teams cuenta como implementación responsive. Es una pregunta
   de un minuto que elimina el riesgo por completo. **Preguntar es más barato que asumir.**

**Beneficio no obvio:** dos canales sobre un mismo núcleo es la **demostración empírica** del
ADR-004. En sustentación: *"mi dominio no sabe si le habla Teams o un navegador — aquí está la
prueba, dos frontends y cero cambios en el núcleo."* Vale más que cualquier diagrama.

**Nota sobre el frontend:** la propuesta original (`Proyecto idea.pdf`) dice **React**, no Angular.
Corrección aceptada. Tensión pendiente de resolver en F4: Iker domina Angular y no React; en una
ventana de 8 semanas, el framework que ya se domina suele valer más que el que aparece en un slide.
Decisión aplazada hasta F4.

---

## 3. Arquitectura del sistema

```
┌─────────────────────────────────────────────────┐
│  Microsoft Teams  (o Angular, plan de contingencia) │
└────────────────────┬────────────────────────────┘
                     │  HTTPS
┌────────────────────▼────────────────────────────┐
│  ADAPTADOR DE BOT  — delgado, sin lógica (ADR-001) │
└────────────────────┬────────────────────────────┘
┌────────────────────▼────────────────────────────┐
│  FastAPI  /  api                                 │
├──────────────────────────────────────────────────┤
│  services/  ORQUESTADOR                          │
│    ¿responder directo? ¿buscar? ¿consultar Graph?│
├──────────────────────────────────────────────────┤
│  ports/   LLMProvider · TaskSource · VectorStore │
├──────────────────────────────────────────────────┤
│  adapters/                                       │
│    ├── Graph: Planner · To Do · Calendario · Chat│
│    ├── Ingesta: PDF/XLSX → chunks → embeddings   │
│    └── LLM: Azure OpenAI | OpenAI | Ollama       │
└────────────────────┬─────────────────────────────┘
                     ▼
        MongoDB Atlas  (docs + vectores + historial)
```

---

## 4. Hoja de ruta

> ⚠️ **REESCRITA EL 2-SEP-2026.** La versión anterior (14 semanas hasta noviembre) se construyó
> **sin haber leído `Definicion del curso.pdf`**. Error de planeación del mentor: se armó un
> cronograma sin leer la rúbrica que lo califica. Es el mismo error que se le venía señalando a
> Iker — asumir en vez de verificar. Queda registrado como precedente.

### 4.1 Lo que exige la rúbrica del curso (fuente: `Definicion del curso.pdf`)

| Entregable | Fecha | Estado |
|---|---|---|
| E1 — MVP y definiciones técnicas | 22 jul | ✅ Entregado (`Proyecto idea.pdf`) |
| E2 — OKR y buyer persona (Mural) | 29 jul | ❓ Sin verificar |
| E3 — Prototipo funcional con todas las pantallas | 12 ago | ❓ Sin verificar |
| E4 — User Story Mapping + Historias de Usuario | 26 ago | ❓ Sin verificar |
| **E-final — Implementación + documentación** | **2 sep → 28 oct** | 🟡 **En curso** |

**Requisitos textuales de la entrega final:**
- *"Implementación **responsive (Desk y Mobile)** funcional de la solución digital en ambientes de desarrollo"*
- Documentación: **definición técnica de arquitectura**, **diagrama de clases**, **diagrama de casos de uso**, **diagrama de base de datos**
- *"Se realizan entregas cada dos semanas"* → checkpoints: **16 sep · 30 sep · 14 oct · 28 oct**

**Deuda documental identificada:** los tres diagramas exigidos no existían en el plan. Se incorporan
a la fase de cierre. No son burocracia: son nota.

### 4.2 Hoja de ruta vigente — 8 semanas

| Fase | Ventana | Objetivo | Criterio de "hecho" |
|---|---|---|---|
| **F1 — Plomería de Teams + esqueleto** | 2–16 sep | Ver algo vivo dentro de Teams y fijar la estructura | Bot *echo* respondiendo en el tenant propio + estructura hexagonal creada |
| **F2 — Núcleo con IA** | 16–30 sep | FastAPI + LLM + Mongo detrás de puertos | El bot de Teams responde con Gemini real, vía el núcleo |
| **F3 — Graph delegado** | 30 sep–14 oct | Agregador de `Pendiente` | *"¿Qué tengo esta semana?"* devuelve Planner + To Do + Calendario unificados |
| **F4 — Web responsive, docs y QA** | 14–28 oct | Cumplir rúbrica y blindar | Frontend web responsive, 3 diagramas, tests verdes, demo ensayada |

**Recorte explícito:** el **RAG sobre documentos (PDF/Excel) queda fuera del alcance calificado.**
Entra solo si sobra tiempo, o se demuestra como prueba de concepto en la sustentación.
Es el sacrificio consciente que impone la ventana de 8 semanas. Duele para el portafolio; se
recupera después de la entrega, con el repo ya público y sin presión de nota.

### 4.3 Inversión del orden — decisión del 2-sep-2026

El plan original ponía Teams en la fase 4. **Se invierte por decisión del tech lead:** Teams pasa a
la fase 1.

**Justificación técnica que respalda la decisión:** la propia bitácora (cierre de OT-01) había
clasificado el SDK de bot de Teams para Python como *"el riesgo más caro del plan"*, con la
instrucción de probarlo mediante un hola-mundo desechable **temprano**. Adelantarlo no contradice
el plan: **ejecuta el plan de mitigación de riesgos antes de lo previsto.**

**Regla que sigue vigente y no se negocia:** el spike de Teams es **código desechable en carpeta
aparte**. El scaffold del Toolkit **no** se convierte en la base del proyecto. Un spike responde una
pregunta y se borra; si se queda, impone su forma al sistema y destruye el ADR-001.

---

## 5. Reparto del equipo

**Principio de asignación:** el trabajo de Julián y Antonio es **real y valioso**, pero está deliberadamente **fuera de la ruta crítica**. Si no entregan, el proyecto se sustenta igual. Cada paquete tiene plantilla y criterio de aceptación para que "no supe qué hacer" no sea una excusa disponible.

### Iker — Tech Lead (ruta crítica)
- Arquitectura y todos los ADR.
- Orquestador, capa de servicios y modelo de dominio.
- Adaptadores de Graph y autenticación delegada.
- Motor de RAG.
- Code review de absolutamente todo.

### Julián — Ingesta de documentos
**Paquete cerrado, sin dependencias del resto del sistema.**
- Librería de funciones puras: archivo → texto limpio estructurado.
- Soporte PDF y XLSX. Manejo de archivos corruptos, vacíos y sin texto (escaneados).
- Tests unitarios propios con un corpus de ejemplos.
- **Aceptación:** `extraer_texto(ruta) -> list[Fragmento]` con tests verdes y ≥5 casos borde cubiertos.
- **Por qué no bloquea:** Iker trabaja con un *stub* que devuelve texto fijo hasta que esté listo.

### Antonio — QA y documentación
**Paquete cerrado, no requiere escribir código de producción.**
- **Golden dataset**: 40+ preguntas reales de estudiantes con la respuesta esperada. *Este es el entregable más valioso del proyecto después del núcleo* — sin él no hay forma de medir si la IA responde bien.
- Batería de pruebas de **prompt injection / jailbreak**: intentos de sacar al bot de su contexto.
- Casos de **control de acceso**: ¿puede el usuario A ver datos del usuario B? (OWASP #1, *Broken Access Control*).
- Manual de usuario y guía de instalación para administradores de TI.
- **Aceptación:** documento versionado en el repo, en formato tabla, revisado por Iker.

### Ambos
- Encuesta a 15+ estudiantes sobre su gestión de pendientes. Es la **evidencia de necesidad** que sustenta el problema ante el docente.
- Diapositivas de la sustentación final.

---

## 6. Riesgos vivos

| # | Riesgo | Impacto | Mitigación | Estado |
|---|---|---|---|---|
| R1 | Tenant UPB bloquea apps personalizadas | Alto | ADR-003: tenant propio | Mitigado por diseño |
| R2 | Permisos de Graph denegados | Crítico | ADR-002: solo delegado | Mitigado por diseño |
| R3 | Sin acceso a Azure OpenAI | Medio | ADR-006: proveedor intercambiable | Mitigado por diseño |
| R4 | SDK de bot Python inmaduro | Medio | ADR-001: capa de bot delgada | Vigilar en F4 |
| R5 | Compañeros no entregan | Medio | Trabajo fuera de ruta crítica | Vigilar continuo |
| R6 | Iker es nuevo en Python idiomático | Medio | Tipado estricto + mypy + code review | Vigilar en F1 |
| R7 | El LLM alucina fechas de entrega | Alto | Campo `confianza` + citación obligatoria | Vigilar en F3 |

---

## 7. Preguntas de sustentación a preparar

1. *"¿Por qué esto y no Microsoft Copilot, que ya viene integrado en Teams?"*
2. *"¿Dónde se almacenan los documentos y qué pasa si el modelo alucina una fecha de entrega?"*
3. *"¿Cómo mides que el asistente responde bien? Dame una métrica."* ← **La que tumba proyectos de IA.**
4. *"¿Por qué monolito y no microservicios?"*
5. *"Si mañana la universidad usa Google Classroom, ¿cuánto hay que reescribir?"*
6. *"¿Cómo garantizas que un usuario no vea los pendientes de otro?"*

---

## 8. Glosario

| Término | Definición |
|---|---|
| **RAG** | *Retrieval-Augmented Generation*. Buscar fragmentos relevantes en tus documentos y pasárselos al modelo como contexto. Es la diferencia entre un examen de memoria y uno a libro abierto con citas obligatorias. |
| **Embedding** | Representación numérica de un texto que captura su significado. Textos con sentido parecido quedan cerca en el espacio vectorial. |
| **Chunking** | Partir un documento en fragmentos del tamaño adecuado para buscar y para caber en el contexto del modelo. Mal hecho, arruina el RAG entero. |
| **Auth delegada / on-behalf-of** | La app actúa *como el usuario*, con sus permisos. Opuesto a permisos de aplicación, donde la app actúa por sí misma sobre toda la organización. |
| **Tenant** | La instancia de Microsoft 365 de una organización. La UPB tiene el suyo; nosotros crearemos el nuestro. |
| **MSA vs Work/School** | Cuenta de consumidor (@outlook.com) vs cuenta organizacional. Solo la segunda tiene Teams empresarial y API de Graph útil. |
| **RSC** | *Resource-Specific Consent*. El dueño de un equipo autoriza una app solo sobre ese equipo, sin pasar por el admin del tenant. |
| **Protected API** | API de Graph con datos sensibles que exige validación adicional de Microsoft mediante formulario. |
| **ISV** | *Independent Software Vendor*. Proveedor cuyo software se instala en el tenant del cliente. |
| **ADR** | *Architecture Decision Record*. Registro de una decisión de arquitectura con su contexto y sus alternativas descartadas. |
| **Puerto / Adaptador** | Puerto = interfaz que define el núcleo. Adaptador = implementación concreta contra tecnología externa. |
| **Golden dataset** | Conjunto de preguntas con respuesta esperada, usado para medir objetivamente la calidad de un sistema de IA. |
| **Prompt injection** | Ataque en que el usuario manipula al modelo para que ignore sus instrucciones. |
| **YAGNI** | *You Aren't Gonna Need It*. No construyas hoy lo que no necesitas hoy. |

---

## 9. Convenciones del repositorio

- **Commits**: *Conventional Commits* (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`).
- **Ramas**: `main` protegida. Trabajo en `feat/nombre`. Merge vía PR, siempre.
- **Los ADR viven en el repo**, en `docs/adr/`. Cada uno numerado e inmutable: si cambia una decisión, se escribe un ADR nuevo que supersede al anterior. No se reescribe la historia.
- **README** con: problema, demo en GIF, arquitectura, cómo correrlo localmente, guía de instalación para administradores. Esta es la cara del portafolio.
- **Nada de secretos en el repo.** `.env` en `.gitignore` desde el commit uno. Un token de Microsoft filtrado en GitHub público es un incidente de seguridad real.

---

## ADR-010 — Precarga de sugerencias con consentimiento

**Estado:** aceptado  
**Fecha:** 14-oct-2026

### Contexto

Analizar todos los chats al ejecutar `revisar` puede tardar cuando el usuario
tiene muchas conversaciones. Se necesita que la bandeja responda rápido, sin
guardar el contenido de los mensajes ni analizar conversaciones sin permiso.

### Decisión

Mientras `vigilancia_activa` sea `true`, un worker separado actualizará las
sugerencias del usuario como máximo cada 30 minutos.

El worker:

- Lee únicamente mensajes de los últimos 7 días.
- Procesa como máximo 300 mensajes por usuario en cada ejecución.
- Solo llama al modelo si encuentra mensajes nuevos o modificados.
- Guarda sugerencias y metadatos de sincronización, nunca el cuerpo de los
  mensajes ni el prompt.
- Conserva `mensaje_id`, `url_mensaje`, `ultima_precarga_en` y el estado de
  cada sugerencia para evitar proponer de nuevo una sugerencia descartada.
- Se detiene para el usuario en cuanto ejecute `no vigilar`.
- Registra errores sin exponer mensajes ni bloquear el bot.

`revisar` muestra primero las sugerencias previamente calculadas y solicita una
actualización no bloqueante. Por eso la respuesta no espera la llamada al modelo.

### Consecuencias

Se añade un contenedor worker al despliegue y una colección de estado de
precarga. La vigilancia continúa siendo opcional, revocable y limitada. El
texto de Teams solo existe en memoria durante cada ejecución y se descarta al
terminar.
