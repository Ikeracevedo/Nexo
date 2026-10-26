"""Contenido de la landing pública de Nexo."""

PAGINA_INICIO = """<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <meta name="description" content="Nexo organiza los compromisos importantes que aparecen en tus conversaciones de Microsoft Teams.">
    <title>Nexo | Tu asistente en Teams</title>
    <style>
      :root { --ink:#151c42; --blue:#343e9e; --violet:#6c64dc; --gold:#f4b63d; --mist:#f6f7ff; --line:#dfe2fa; --white:#fff; }
      * { box-sizing:border-box; }
      html { scroll-behavior:smooth; }
      body { margin:0; color:var(--ink); background:var(--mist); font-family:Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
      a { color:inherit; text-decoration:none; }
      .wrap { width:min(1120px, calc(100% - 40px)); margin:0 auto; }
      .nav { height:76px; display:flex; align-items:center; justify-content:space-between; }
      .brand { display:flex; align-items:center; gap:10px; font-weight:800; font-size:1.25rem; letter-spacing:-.04em; }
      .brand img { width:42px; height:42px; border-radius:13px; box-shadow:0 6px 16px #252d7330; }
      .nav a:last-child { padding:10px 15px; border:1px solid var(--line); border-radius:999px; font-size:.9rem; font-weight:700; background:#ffffffb5; }
      .hero { min-height:calc(100vh - 76px); display:grid; grid-template-columns:1.05fr .95fr; align-items:center; gap:48px; padding:54px 0 82px; }
      .eyebrow { display:inline-flex; gap:8px; align-items:center; padding:8px 12px; border:1px solid #d9d9fb; border-radius:999px; background:#fff; color:#4844aa; font-size:.86rem; font-weight:750; }
      .dot { width:8px; height:8px; border-radius:50%; background:var(--gold); box-shadow:0 0 0 4px #fddf9e75; }
      h1 { max-width:690px; margin:20px 0; font-size:clamp(3rem, 6vw, 5.7rem); line-height:.96; letter-spacing:-.07em; }
      h1 span { color:var(--violet); }
      .lead { max-width:590px; color:#535c7b; font-size:clamp(1.05rem, 1.5vw, 1.22rem); line-height:1.65; }
      .actions { display:flex; flex-wrap:wrap; gap:12px; margin-top:30px; }
      .button { display:inline-flex; align-items:center; justify-content:center; gap:9px; min-height:48px; padding:0 20px; border-radius:13px; font-weight:800; transition:transform .18s ease, box-shadow .18s ease; }
      .button:hover { transform:translateY(-2px); }
      .button.primary { color:#fff; background:var(--blue); box-shadow:0 11px 22px #343e9e42; }
      .button.secondary { border:1px solid var(--line); background:#fff; }
      .hint { margin:15px 0 0; color:#6a7290; font-size:.88rem; }
      .stage { position:relative; min-height:510px; display:grid; place-items:center; }
      .halo { position:absolute; width:min(430px, 90%); aspect-ratio:1; border-radius:50%; background:radial-gradient(circle at 38% 33%, #fff 0 9%, #e5e6ff 42%, #c9c9fb 100%); }
      .mascot { position:relative; width:min(305px, 72%); border-radius:34px; filter:drop-shadow(0 28px 22px #22266631); transform:rotate(-3deg); }
      .bubble { position:absolute; right:0; bottom:72px; width:190px; padding:16px; border:1px solid #ffffffaa; border-radius:17px; background:#fffffff0; box-shadow:0 18px 42px #252d7321; font-size:.9rem; line-height:1.45; }
      .bubble strong { display:block; margin-bottom:4px; color:#4844aa; }
      .spark { position:absolute; top:65px; right:42px; width:22px; height:22px; background:var(--gold); clip-path:polygon(50% 0, 61% 39%, 100% 50%, 61% 61%, 50% 100%, 39% 61%, 0 50%, 39% 39%); }
      .section { padding:96px 0; }
      .section-header { max-width:650px; margin-bottom:34px; }
      h2 { margin:0 0 12px; font-size:clamp(2rem, 4vw, 3.2rem); letter-spacing:-.055em; line-height:1; }
      .section-header p { color:#59617c; line-height:1.6; }
      .cards { display:grid; grid-template-columns:repeat(3, 1fr); gap:18px; }
      .card { min-height:240px; padding:26px; border:1px solid var(--line); border-radius:22px; background:#fff; }
      .icon { display:grid; place-items:center; width:46px; height:46px; border-radius:14px; background:#e9e9ff; color:#3934a6; font-size:1.35rem; }
      .card h3 { margin:24px 0 9px; font-size:1.16rem; letter-spacing:-.025em; }
      .card p { margin:0; color:#626a84; line-height:1.55; font-size:.95rem; }
      .how { border-radius:28px; padding:clamp(26px, 5vw, 58px); color:#fff; background:linear-gradient(125deg, #171d4a, #363a9a 65%, #5955cf); overflow:hidden; position:relative; }
      .how:after { content:""; position:absolute; right:-130px; bottom:-175px; width:370px; height:370px; border:38px solid #ffffff12; border-radius:50%; }
      .how h2 { max-width:520px; }
      .steps { position:relative; z-index:1; display:grid; grid-template-columns:repeat(3, 1fr); gap:22px; margin-top:42px; }
      .step { padding-top:15px; border-top:1px solid #ffffff45; }
      .step b { display:inline-grid; place-items:center; width:29px; height:29px; margin-bottom:13px; border-radius:50%; background:var(--gold); color:#29265e; font-size:.86rem; }
      .step p { margin:0; color:#e6e8ff; line-height:1.5; }
      .command { display:inline-block; margin-top:8px; padding:5px 8px; border-radius:7px; background:#ffffff1b; color:#fff; font:700 .85rem ui-monospace, SFMono-Regular, Menlo, monospace; }
      .privacy { display:flex; align-items:center; gap:16px; margin-top:42px; padding:18px 20px; border-radius:15px; background:#ffffff14; color:#e8eaff; font-size:.92rem; line-height:1.45; }
      .privacy span { font-size:1.35rem; }
      footer { padding:28px 0 38px; color:#747b96; font-size:.88rem; }
      @media (max-width:780px) { .hero { grid-template-columns:1fr; padding-top:28px; } .stage { min-height:380px; order:-1; } .bubble { right:4%; bottom:26px; } .cards, .steps { grid-template-columns:1fr; } .section { padding:70px 0; } }
      @media (max-width:440px) { .wrap { width:min(100% - 28px, 1120px); } .nav a:last-child { display:none; } .stage { min-height:330px; } h1 { font-size:3.05rem; } }
    </style>
  </head>
  <body>
    <header class="wrap nav">
      <a class="brand" href="/" aria-label="Inicio de Nexo"><img src="/static/nexo.png" alt="Mascota de Nexo">Nexo</a>
      <a href="#como-empezar">Cómo empezar</a>
    </header>
    <main>
      <section class="wrap hero">
        <div>
          <div class="eyebrow"><i class="dot"></i>Tu asistente dentro de Teams</div>
          <h1>Tu día, <span>en orden.</span></h1>
          <p class="lead">Nexo encuentra compromisos en tus conversaciones de Microsoft Teams y los convierte en pendientes claros, para que nada importante se quede entre mensajes.</p>
          <div class="actions"><a class="button primary" href="#como-empezar">Empezar con Nexo <span>→</span></a><a class="button secondary" href="#que-hace">Ver cómo funciona</a></div>
          <p class="hint">Sin cambiar tu forma de trabajar. Solo conversa en Teams.</p>
        </div>
        <div class="stage" aria-hidden="true"><div class="halo"></div><i class="spark"></i><img class="mascot" src="/static/nexo.png" alt=""><div class="bubble"><strong>Todo bajo control</strong>Detecto lo que acordaste y te lo recuerdo cuando importa.</div></div>
      </section>
      <section id="que-hace" class="wrap section">
        <div class="section-header"><h2>Menos seguimiento manual. Más claridad.</h2><p>Nexo trabaja en el espacio donde ya colaboras, con sugerencias que tú decides si convertir en pendientes.</p></div>
        <div class="cards"><article class="card"><div class="icon">✦</div><h3>Lee con intención</h3><p>Con tu autorización, analiza chats para encontrar fechas, entregables y compromisos relevantes.</p></article><article class="card"><div class="icon">✓</div><h3>Propone, no impone</h3><p>Te muestra pendientes sugeridos con su nivel de confianza y enlace a la conversación de origen.</p></article><article class="card"><div class="icon">◷</div><h3>Te da contexto</h3><p>Consulta tu semana y ordena lo urgente para que tengas una vista útil de lo que sigue.</p></article></div>
      </section>
      <section id="como-empezar" class="wrap section"><div class="how"><h2>Empieza en menos de un minuto.</h2><div class="steps"><div class="step"><b>1</b><p>Abre Nexo desde Microsoft Teams y conecta tu cuenta.</p><span class="command">conectar</span></div><div class="step"><b>2</b><p>Autoriza el análisis de tus conversaciones cuando Nexo te lo solicite.</p><span class="command">vigilar</span></div><div class="step"><b>3</b><p>Revisa los pendientes que Nexo detectó y conserva solo los que te sirven.</p><span class="command">revisar</span></div></div><div class="privacy"><span>🔒</span><div><strong>Tú mantienes el control.</strong><br>La vigilancia se activa y se desactiva con tus propios comandos; Nexo solo usa los datos necesarios para ayudarte.</div></div></div></section>
    </main>
    <footer class="wrap">Nexo · Tu asistente para tenerlo todo organizado en un solo lugar.</footer>
  </body>
</html>"""
