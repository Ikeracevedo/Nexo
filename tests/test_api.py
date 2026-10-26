from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_landing_presenta_identidad_y_primeros_pasos() -> None:
    respuesta = cliente.get("/")
    assert respuesta.status_code == 200
    assert "Nexo" in respuesta.text
    assert "conectar" in respuesta.text
    assert "vigilar" in respuesta.text


def test_landing_expone_icono_de_nexo() -> None:
    respuesta = cliente.get("/static/nexo.png")
    assert respuesta.status_code == 200
    assert respuesta.headers["content-type"] == "image/png"


def test_health_responde_200() -> None:
    r = cliente.get("/health")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"


def test_health_no_depende_de_fuentes_externas() -> None:
    """Sonda de vida (liveness): mide el proceso, no sus dependencias."""
    assert cliente.get("/health").status_code == 200


def test_agenda_devuelve_pendientes_del_adaptador_de_ejemplo() -> None:
    r = cliente.get("/api/agenda")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["total"] == 4
    assert cuerpo["esta_completa"] is True


def test_agenda_marca_el_pendiente_inferido() -> None:
    """La tesis del proyecto, verificada: se distingue un hecho de
    una inferencia, y la API lo expone."""
    cuerpo = cliente.get("/api/agenda").json()
    inferidos = [p for p in cuerpo["pendientes"] if p["es_inferido"]]
    assert len(inferidos) == 1
    assert inferidos[0]["fuente"] == "MENSAJE"
    assert inferidos[0]["confianza"] < 1.0


def test_todo_pendiente_tiene_url_de_origen() -> None:
    """Trazabilidad obligatoria, verificada en la frontera HTTP."""
    cuerpo = cliente.get("/api/agenda").json()
    for p in cuerpo["pendientes"]:
        assert p["url_origen"], f"Pendiente sin origen: {p['id']}"


def test_openapi_se_genera() -> None:
    assert cliente.get("/openapi.json").status_code == 200
