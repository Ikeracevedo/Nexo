"""La tarjeta de Teams se testea sin Teams, sin red y sin servidor.

Si estos tests necesitaran un tenant conectado, el adaptador estaria
mal cortado: significaria que la presentacion depende de la plataforma
en vez de depender solo del dominio.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from app.bot.tarjeta_agenda import tarjeta_agenda
from app.dominio.agenda import Agenda, FuenteFallida
from app.dominio.pendiente import FuentePendiente, Pendiente

AHORA = datetime(2026, 9, 8, 10, 0, 0)


def _p(id_: str, confianza: float = 1.0, dias: int | None = 2) -> Pendiente:
    return Pendiente(
        id=id_,
        titulo=f"Tarea {id_}",
        fuente=FuentePendiente.PLANNER if confianza == 1.0 else FuentePendiente.MENSAJE,
        url_origen=f"https://teams.microsoft.com/l/entity/{id_}",
        vence=None if dias is None else AHORA + timedelta(days=dias),
        confianza=confianza,
    )


def _texto(card: Any) -> str:
    """Aplana la tarjeta a texto para poder afirmar sobre su contenido."""
    return str(card.model_dump(exclude_none=True, by_alias=True))


# --- Camino feliz -----------------------------------------------------


def test_la_tarjeta_muestra_el_conteo_de_pendientes() -> None:
    agenda = Agenda(pendientes=(_p("a"), _p("b")), fuentes_consultadas=("planner",))
    assert "2 pendientes" in _texto(tarjeta_agenda(agenda, AHORA))


def test_distingue_confirmados_de_inferidos_en_el_encabezado() -> None:
    agenda = Agenda(
        pendientes=(_p("a"), _p("b", confianza=0.72)),
        fuentes_consultadas=("planner", "mensajes"),
    )
    t = _texto(tarjeta_agenda(agenda, AHORA))
    assert "1 confirmados" in t
    assert "1 inferidos" in t


def test_todo_pendiente_lleva_su_enlace_de_origen() -> None:
    """Trazabilidad obligatoria (ADR-005), verificada en la presentacion."""
    agenda = Agenda(pendientes=(_p("a"), _p("b")), fuentes_consultadas=("planner",))
    t = _texto(tarjeta_agenda(agenda, AHORA))
    assert "https://teams.microsoft.com/l/entity/a" in t
    assert "https://teams.microsoft.com/l/entity/b" in t
    assert t.count("Ver origen") == 2


# --- La tesis del proyecto: hecho != inferencia ------------------------


def test_un_pendiente_inferido_sale_en_amarillo_y_con_su_porcentaje() -> None:
    agenda = Agenda(pendientes=(_p("m", confianza=0.72),), fuentes_consultadas=("mensajes",))
    t = _texto(tarjeta_agenda(agenda, AHORA))
    assert "72% — inferido" in t
    assert "Warning" in t
    assert "Nexo no confirma este pendiente" in t


def test_un_pendiente_confirmado_no_lleva_advertencia() -> None:
    agenda = Agenda(pendientes=(_p("p"),), fuentes_consultadas=("planner",))
    t = _texto(tarjeta_agenda(agenda, AHORA))
    assert "Confirmado (dato estructurado)" in t
    assert "no confirma este pendiente" not in t


# --- La regla no negociable: fallo != vacio ---------------------------


def test_una_agenda_incompleta_declara_que_fuente_fallo() -> None:
    """Sin este bloque, una agenda incompleta se veria identica a una
    agenda vacia y Brujula estaria mintiendo por omision."""
    agenda = Agenda(
        pendientes=(_p("a"),),
        fuentes_consultadas=("calendario",),
        fuentes_fallidas=(FuenteFallida("planner", "403 Forbidden"),),
    )
    t = _texto(tarjeta_agenda(agenda, AHORA))
    assert "No pude consultar" in t
    assert "planner" in t
    assert "no pude preguntar" in t


def test_una_agenda_completa_no_muestra_el_aviso() -> None:
    agenda = Agenda(pendientes=(_p("a"),), fuentes_consultadas=("planner",))
    assert "No pude consultar" not in _texto(tarjeta_agenda(agenda, AHORA))


def test_agenda_vacia_pero_completa_dice_que_no_hay_pendientes() -> None:
    agenda = Agenda(pendientes=(), fuentes_consultadas=("planner",))
    t = _texto(tarjeta_agenda(agenda, AHORA))
    assert "No tienes pendientes" in t
    assert "No pude consultar" not in t


def test_agenda_vacia_por_fallo_NO_dice_que_no_hay_pendientes() -> None:
    """El bug mas caro posible del proyecto, cerrado con un test:
    'no tienes pendientes' cuando la verdad es 'no pude preguntar'."""
    agenda = Agenda(
        pendientes=(),
        fuentes_consultadas=(),
        fuentes_fallidas=(FuenteFallida("planner", "403 Forbidden"),),
    )
    t = _texto(tarjeta_agenda(agenda, AHORA))
    assert "No tienes pendientes" not in t
    assert "No pude consultar" in t


# --- Casos borde ------------------------------------------------------


def test_un_pendiente_sin_fecha_se_muestra_como_sin_fecha() -> None:
    agenda = Agenda(pendientes=(_p("a", dias=None),), fuentes_consultadas=("todo",))
    assert "Sin fecha" in _texto(tarjeta_agenda(agenda, AHORA))


def test_las_fechas_se_muestran_en_relativo() -> None:
    agenda = Agenda(
        pendientes=(_p("hoy", dias=0), _p("man", dias=1), _p("lej", dias=4)),
        fuentes_consultadas=("planner",),
    )
    t = _texto(tarjeta_agenda(agenda, AHORA))
    assert "(hoy)" in t
    assert "(mañana)" in t
    assert "en 4 días" in t


def test_si_falta_autorizacion_la_tarjeta_dice_como_arreglarlo() -> None:
    agenda = Agenda(
        pendientes=(),
        fuentes_consultadas=(),
        fuentes_fallidas=(
            FuenteFallida("calendario", "falta el permiso", requiere_autorizacion=True),
        ),
    )
    t = _texto(tarjeta_agenda(agenda, AHORA))
    assert "Falta tu autorización" in t
    assert "calendario" in t
    assert "conectar" in t


def test_un_fallo_tecnico_NO_pide_conectar_la_cuenta() -> None:
    """Distinguir importa: ofrecerle 'conectar tu cuenta' a alguien cuyo
    problema es un 500 de Graph lo manda a dar vueltas sin arreglar nada."""
    agenda = Agenda(
        pendientes=(),
        fuentes_consultadas=(),
        fuentes_fallidas=(FuenteFallida("calendario", "Graph respondio 500"),),
    )
    t = _texto(tarjeta_agenda(agenda, AHORA))
    assert "Falta tu autorización" not in t
