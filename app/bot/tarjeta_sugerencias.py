"""Tarjeta separada para inferencias que el usuario aún no confirma."""

from __future__ import annotations

from datetime import date, datetime
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

from app.dominio.sugerencia import DeQuien, Sugerencia

ColorTexto = Literal["Default", "Dark", "Light", "Accent", "Good", "Warning", "Attention"]


def _texto_fecha(fecha: date | None, ahora: datetime) -> str:
    if fecha is None:
        return "Sin fecha identificada"

    dias = (fecha - ahora.date()).days
    if dias == 0:
        return "hoy"
    if dias == 1:
        return "mañana"
    return f"en {dias} días" if dias > 1 else f"hace {abs(dias)} días"


def _bloque_sugerencia(sugerencia: Sugerencia, ahora: datetime) -> Container:
    de_quien = (
        "tu compromiso" if sugerencia.de_quien is DeQuien.USUARIO else "compromiso de otra persona"
    )

    acciones: list[Action] = [
        OpenUrlAction(title="Ver mensaje", url=sugerencia.url_mensaje),
        ExecuteAction(
            title="Aceptar",
            verb="aceptar_sugerencia",
            data={
                "action": "aceptar_sugerencia",
                "sugerencia_id": sugerencia.id,
            },
        ),
        ExecuteAction(
            title="Descartar",
            verb="descartar_sugerencia",
            data={
                "action": "descartar_sugerencia",
                "sugerencia_id": sugerencia.id,
            },
        ),
    ]

    items: list[CardElement] = [
        TextBlock(
            text=sugerencia.texto,
            weight="Bolder",
            size="Medium",
            wrap=True,
            color="Warning",
        ),
        FactSet(
            facts=[
                Fact(title="Conversación", value=sugerencia.conversacion),
                Fact(title="Fecha", value=_texto_fecha(sugerencia.fecha, ahora)),
                Fact(title="Confianza", value=f"{int(sugerencia.confianza * 100)}%"),
                Fact(title="Tipo", value=de_quien),
            ]
        ),
        TextBlock(
            text="Esto es una sugerencia de IA. Verifica el mensaje antes de aceptarla.",
            wrap=True,
            size="Small",
            color="Warning",
        ),
        ActionSet(actions=acciones),
    ]

    return Container(items=items, style="warning", show_border=True, spacing="Medium")


def tarjeta_sugerencias(
    sugerencias: list[Sugerencia],
    ahora: datetime,
    nombre: str = "Nexo",
) -> AdaptiveCard:
    """Construye una bandeja visualmente separada de la agenda confirmada."""
    cuerpo: list[CardElement] = [
        TextBlock(
            text="💡 Posibles pendientes",
            size="Large",
            weight="Bolder",
            wrap=True,
            color="Warning",
        ),
        TextBlock(
            text=(
                f"{nombre} los encontró en tus conversaciones. "
                "No entran a tu agenda hasta que tú los aceptes."
            ),
            wrap=True,
            is_subtle=True,
        ),
    ]

    if not sugerencias:
        cuerpo.append(
            TextBlock(
                text="No encontré compromisos nuevos para proponerte.",
                wrap=True,
                spacing="Medium",
            )
        )
    else:
        cuerpo.extend(_bloque_sugerencia(sugerencia, ahora) for sugerencia in sugerencias)

    return AdaptiveCard(body=cuerpo)
