"""La bandeja de sugerencias se prueba sin Teams ni servicios externos."""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from app.bot.tarjeta_sugerencias import tarjeta_sugerencias
from app.dominio.sugerencia import DeQuien, Sugerencia

AHORA = datetime(2026, 10, 14, 12, tzinfo=UTC)


def _sugerencia() -> Sugerencia:
    return Sugerencia(
        id="507f1f77bcf86cd799439011",
        texto="Enviar el informe",
        confianza=0.9,
        id_mensaje="mensaje-1",
        url_mensaje="https://teams.microsoft.com/l/message/chat/mensaje-1",
        conversacion="Proyecto TIC",
        de_quien=DeQuien.USUARIO,
        fecha=date(2026, 10, 15),
    )


def _texto(tarjeta: Any) -> str:
    return str(tarjeta.model_dump(exclude_none=True, by_alias=True))


def test_la_sugerencia_se_muestra_en_amarillo_y_separada_de_la_agenda() -> None:
    texto = _texto(tarjeta_sugerencias([_sugerencia()], AHORA))

    assert "Posibles pendientes" in texto
    assert "Enviar el informe" in texto
    assert "Warning" in texto
    assert "No entran a tu agenda" in texto


def test_la_sugerencia_tiene_enlace_y_acciones_con_el_id_real() -> None:
    sugerencia = _sugerencia()
    texto = _texto(tarjeta_sugerencias([sugerencia], AHORA))

    assert sugerencia.url_mensaje in texto
    assert "aceptar_sugerencia" in texto
    assert "descartar_sugerencia" in texto
    assert sugerencia.id is not None
    assert sugerencia.id in texto


def test_una_bandeja_vacia_lo_declara_con_honestidad() -> None:
    texto = _texto(tarjeta_sugerencias([], AHORA))

    assert "No encontré compromisos nuevos" in texto
    assert "aceptar_sugerencia" not in texto


def test_indica_si_el_compromiso_es_del_usuario_o_de_otro() -> None:
    ajena = Sugerencia(
        id="507f1f77bcf86cd799439012",
        texto="Julian enviará el informe",
        confianza=0.7,
        id_mensaje="mensaje-2",
        url_mensaje="https://teams.microsoft.com/l/message/chat/mensaje-2",
        conversacion="Proyecto TIC",
        de_quien=DeQuien.OTRO,
    )

    texto = _texto(tarjeta_sugerencias([ajena], AHORA))

    assert "compromiso de otra persona" in texto
