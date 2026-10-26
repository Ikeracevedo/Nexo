from __future__ import annotations

from pytest import MonkeyPatch

from app.adaptadores import cliente_mongo


def test_reutiliza_un_cliente_por_uri_y_configuracion(monkeypatch: MonkeyPatch) -> None:
    clientes: list[object] = []

    def crear_cliente(*args: object, **kwargs: object) -> object:
        cliente = object()
        clientes.append(cliente)
        assert args == ("mongodb://prueba",)
        assert kwargs["maxPoolSize"] == cliente_mongo.MAX_CONEXIONES_POR_PROCESO
        return cliente

    monkeypatch.setattr(cliente_mongo, "AsyncMongoClient", crear_cliente)
    cliente_mongo.obtener_cliente_mongo.cache_clear()
    try:
        primero = cliente_mongo.obtener_cliente_mongo("mongodb://prueba")
        segundo = cliente_mongo.obtener_cliente_mongo("mongodb://prueba")
    finally:
        cliente_mongo.obtener_cliente_mongo.cache_clear()

    assert primero is segundo
    assert clientes == [primero]
