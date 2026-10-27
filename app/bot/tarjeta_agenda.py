from __future__ import annotations

from datetime import datetime
from typing import Literal

from microsoft_teams.cards import (
    Action,
    ActionSet,
    AdaptiveCard,
    CardElement,
    Container,
    ExecuteAction,
    Fact,
    FactSet,
    OpenUrlAction,
    TextBlock,
)

from app.dominio.agenda import Agenda
from app.dominio.pendiente import FuentePendiente, Pendiente

# El SDK tipa `color` y `style` como Literal cerrados. Anotarlos asi en vez
# de `str` es lo que permite que mypy verifique que no se cuela un valor
# invalido: un "Verde" en vez de "Good" fallaria aqui y no en pantalla.
ColorTexto = Literal["Default", "Dark", "Light", "Accent", "Good", "Warning", "Attention"]
EstiloContenedor = Literal["default", "emphasis", "accent", "good", "attention", "warning"]

_ETIQUETA_FUENTE: dict[FuentePendiente, str] = {
    FuentePendiente.PLANNER: "📋 Planner",
    FuentePendiente.TODO: "✅ To Do",
    FuentePendiente.CALENDARIO: "📅 Calendario",
    FuentePendiente.MENSAJE: "💬 Mensaje de Teams",
    FuentePendiente.PROPIO: "✏️ Propio",
}


def _texto_fecha(vence: datetime | None, ahora: datetime) -> str:
    if vence is None:
        return "Sin fecha"
    dias = (vence.date() - ahora.date()).days
    relativo = {0: "hoy", 1: "mañana"}.get(dias)
    if relativo is None:
        relativo = f"en {dias} días" if dias > 0 else f"hace {abs(dias)} días"
    return f"{vence.strftime('%d/%m %H:%M')} ({relativo})"


def _bloque_pendiente(p: Pendiente, ahora: datetime, nombre: str) -> Container:
    """Un pendiente. El contraste visual ES la tesis del proyecto."""
    hechos = [
        Fact(title="Fuente", value=_ETIQUETA_FUENTE[p.fuente]),
        Fact(title="Vence", value=_texto_fecha(p.vence, ahora)),
    ]

    color: ColorTexto
    estilo: EstiloContenedor
    if p.es_inferido:
        hechos.append(Fact(title="Confianza", value=f"{int(p.confianza * 100)}% — inferido"))
        color, estilo = "Warning", "warning"
    else:
        hechos.append(Fact(title="Confianza", value="Confirmado (dato estructurado)"))
        color, estilo = "Good", "good"

    items: list[CardElement] = [
        TextBlock(text=p.titulo, weight="Bolder", size="Medium", wrap=True, color=color),
        FactSet(facts=hechos),
    ]

    if p.contexto:
        items.append(TextBlock(text=p.contexto, wrap=True, is_subtle=True, size="Small"))

    if p.es_inferido:
        items.append(
            TextBlock(
                text=f"{nombre} no confirma este pendiente. Verifícalo en el origen.",
                wrap=True,
                size="Small",
                color="Warning",
            )
        )

    # Trazabilidad toda afirmacion enlaza a su fuente.
    acciones: list[Action] = [OpenUrlAction(title="Ver origen", url=p.url_origen)]

    if p.fuente is FuentePendiente.PROPIO:
        acciones.extend(
            [
                ExecuteAction(
                    title="Listo",
                    verb="completar_pendiente",
                    data={
                        "action": "completar_pendiente",
                        "pendiente_id": p.id,
                    },
                ),
                ExecuteAction(
                    title="Borrar",
                    verb="borrar_pendiente",
                    data={
                        "action": "borrar_pendiente",
                        "pendiente_id": p.id,
                    },
                ),
            ]
        )

    items.append(ActionSet(actions=acciones))

    return Container(items=items, style=estilo, show_border=True, spacing="Medium")


def _aviso_fuentes_fallidas(agenda: Agenda) -> Container:
    """Declara en la tarjeta lo que Nexo NO pudo consultar.

    Este bloque es la razon de existir del campo `fuentes_fallidas`. Sin el, una agenda
    incompleta se veria identica a una agenda vacia, y
    Nexo estaria mintiendo por omision.
    """
    nombres = ", ".join(f.nombre for f in agenda.fuentes_fallidas)
    por_autorizar = [f.nombre for f in agenda.fuentes_fallidas if f.requiere_autorizacion]

    items: list[CardElement] = [
        TextBlock(
            text=f"⚠ No pude consultar: {nombres}",
            weight="Bolder",
            wrap=True,
            color="Attention",
        ),
        TextBlock(
            text=(
                "Esta lista está incompleta. No significa que no tengas pendientes ahí: "
                "significa que no pude preguntar."
            ),
            wrap=True,
            size="Small",
            is_subtle=True,
        ),
    ]

    if por_autorizar:
        items.append(
            TextBlock(
                text=(
                    f"Falta tu autorización para {', '.join(por_autorizar)}. "
                    "Escribe **conectar** para darla."
                ),
                wrap=True,
                size="Small",
                color="Warning",
            )
        )

    return Container(items=items, style="attention", show_border=True, spacing="Medium")


def _encabezado(agenda: Agenda) -> list[CardElement]:
    confirmados = sum(1 for p in agenda.pendientes if not p.es_inferido)
    inferidos = agenda.total - confirmados
    return [
        TextBlock(text="Tu semana", size="Large", weight="Bolder", wrap=True),
        TextBlock(
            text=(
                f"{agenda.total} pendientes — {confirmados} confirmados, "
                f"{inferidos} inferidos de conversaciones"
            ),
            is_subtle=True,
            wrap=True,
            spacing="None",
        ),
    ]


def tarjeta_agenda(agenda: Agenda, ahora: datetime, nombre: str = "Nexo") -> AdaptiveCard:
    """Construye la tarjeta de "¿que tengo esta semana?".

    `ahora` se recibe como parametro y no se lee del reloj, por el mismo
    motivo que en ServicioAgenda: una funcion que consulta el reloj del
    sistema no se puede testear de forma determinista.
    """
    cuerpo: list[CardElement] = _encabezado(agenda)

    if not agenda.esta_completa:
        cuerpo.append(_aviso_fuentes_fallidas(agenda))

    if agenda.total == 0 and agenda.esta_completa:
        cuerpo.append(
            TextBlock(
                text="No tienes pendientes en los próximos 7 días.",
                wrap=True,
                spacing="Medium",
            )
        )

    cuerpo += [_bloque_pendiente(p, ahora, nombre) for p in agenda.pendientes]

    cuerpo.append(
        TextBlock(
            text=(
                "Fuentes consultadas: " + (", ".join(agenda.fuentes_consultadas) or "ninguna") + "."
            ),
            size="Small",
            is_subtle=True,
            wrap=True,
            spacing="Large",
        )
    )
    return AdaptiveCard(body=cuerpo)
