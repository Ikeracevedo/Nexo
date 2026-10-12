"""La configuracion valida sus invariantes al construirse."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from app.config import Configuracion

GUID_VALIDO = "337859e0-7821-4720-a22d-e2d1d3960bf0"


def test_acepta_un_guid_valido() -> None:
    c = Configuracion(azure_tenant_id=GUID_VALIDO)
    assert c.azure_tenant_id == GUID_VALIDO


def test_acepta_vacio_porque_significa_no_configurado_aun() -> None:
    assert Configuracion(azure_tenant_id="").azure_tenant_id == ""


def test_rechaza_un_guid_al_que_le_falta_un_caracter() -> None:
    """El bug real encontrado en la auditoria del 8-sep: un copiar-pegar
    que perdio el primer caracter. Invisible hasta OT-05."""
    truncado = GUID_VALIDO[1:]  # 35 caracteres
    with pytest.raises(ValidationError, match="GUID"):
        Configuracion(azure_tenant_id=truncado)


def test_rechaza_texto_que_no_es_guid() -> None:
    with pytest.raises(ValidationError, match="GUID"):
        Configuracion(azure_client_id="brujulateams.onmicrosoft.com")


def test_el_mensaje_de_error_dice_cuantos_caracteres_hay() -> None:
    """Un error que no dice que esta mal obliga a adivinar."""
    with pytest.raises(ValidationError) as e:
        Configuracion(azure_tenant_id=GUID_VALIDO[1:])
    assert "35" in str(e.value) and "36" in str(e.value)


def test_una_zona_horaria_invalida_se_rechaza() -> None:
    with pytest.raises(ValueError, match="zona IANA"):
        Configuracion(brujula_zona_horaria="Mordor/Barad-dur")
