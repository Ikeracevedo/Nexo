from __future__ import annotations

import asyncio
from collections.abc import Sequence
from datetime import UTC, datetime
from io import BytesIO
from types import SimpleNamespace

import httpx
import pytest
from docx import Document
from openpyxl import Workbook

from app.adaptadores.extractor_docx import ExtractorDocx
from app.adaptadores.extractor_xlsx import ExtractorXlsx
from app.adaptadores.memoria_en_proceso import MemoriaEnProceso
from app.bot.descarga_adjuntos import descargar_adjuntos, descargar_archivos
from app.dominio.adjunto import (
    MIME_DOCX,
    MIME_XLSX,
    Adjunto,
    AdjuntoNoSoportadoError,
)
from app.servicios.servicio_conversacion import ServicioConversacion

AHORA = datetime(2026, 10, 7, tzinfo=UTC)
TIPO_ARCHIVO = "application/vnd.microsoft.teams.file.download.info"
CONFIG = SimpleNamespace(
    azure_tenant_id="tenant-prueba",
    teams_bot_id="bot-prueba",
    teams_bot_password="secreto-prueba",
)


# --- Extractores ---------------------------------------------------------------


def _xlsx_de_prueba() -> bytes:
    libro = Workbook()
    hoja = libro.active
    hoja.title = "Notas"
    hoja.append(["Alumno", "Nota"])
    hoja.append(["Ana", 4.5])
    hoja.append([None, None])  # fila vacia: se omite
    otra = libro.create_sheet("Otra")
    otra.append(["solo una celda"])
    buffer = BytesIO()
    libro.save(buffer)
    return buffer.getvalue()


def _docx_de_prueba() -> bytes:
    documento = Document()
    documento.add_paragraph("Primer parrafo")
    documento.add_paragraph("")
    documento.add_paragraph("Segundo parrafo")
    tabla = documento.add_table(rows=1, cols=2)
    tabla.rows[0].cells[0].text = "Curso"
    tabla.rows[0].cells[1].text = "TIC 1"
    buffer = BytesIO()
    documento.save(buffer)
    return buffer.getvalue()


def test_extractor_xlsx_lee_hojas_y_omite_filas_vacias() -> None:
    texto = ExtractorXlsx().extraer_texto(_xlsx_de_prueba())

    assert "## Hoja: Notas" in texto
    assert "Alumno | Nota" in texto
    assert "Ana | 4.5" in texto
    assert "## Hoja: Otra" in texto
    assert "solo una celda" in texto
    assert " | \n" not in texto  # la fila vacia no aparece


def test_extractor_docx_lee_parrafos_y_tablas() -> None:
    texto = ExtractorDocx().extraer_texto(_docx_de_prueba())

    assert "Primer parrafo" in texto
    assert "Segundo parrafo" in texto
    assert "Curso | TIC 1" in texto


# --- Servicio ------------------------------------------------------------------


class LLMRegistro:
    nombre_modelo = "registro"

    def __init__(self) -> None:
        self.llamadas: list[tuple[str, list[Adjunto]]] = []

    async def generar(
        self,
        instruccion: str,
        contexto: str,
        adjuntos: Sequence[Adjunto] = (),
    ) -> str:
        self.llamadas.append((contexto, list(adjuntos)))
        return "ok"


class ExtractorFalso:
    def extraer_texto(self, datos: bytes) -> str:
        return datos.decode("utf-8")


class ExtractorRoto:
    def extraer_texto(self, datos: bytes) -> str:
        raise ValueError("archivo corrupto")


def test_el_servicio_convierte_excel_en_texto() -> None:
    llm = LLMRegistro()
    servicio = ServicioConversacion(
        llm, MemoriaEnProceso(), extractor_xlsx=ExtractorFalso()
    )
    xlsx = Adjunto("notas.xlsx", MIME_XLSX, b"datos de la hoja")

    asyncio.run(servicio.responder("c1", "resume", AHORA, [xlsx]))

    contexto, adjuntos = llm.llamadas[0]
    assert adjuntos == []
    assert 'documento "notas.xlsx"' in contexto
    assert "datos de la hoja" in contexto


def test_un_archivo_corrupto_da_un_mensaje_claro() -> None:
    llm = LLMRegistro()
    servicio = ServicioConversacion(
        llm, MemoriaEnProceso(), extractor_docx=ExtractorRoto()
    )
    docx = Adjunto("roto.docx", MIME_DOCX, b"basura")

    with pytest.raises(AdjuntoNoSoportadoError, match="No pude leer"):
        asyncio.run(servicio.responder("c1", "lee", AHORA, [docx]))

    assert llm.llamadas == []


def test_sin_extractor_un_excel_se_rechaza() -> None:
    llm = LLMRegistro()
    servicio = ServicioConversacion(llm, MemoriaEnProceso())
    xlsx = Adjunto("notas.xlsx", MIME_XLSX, b"datos")

    with pytest.raises(AdjuntoNoSoportadoError):
        asyncio.run(servicio.responder("c1", "lee", AHORA, [xlsx]))


# --- Descarga de archivos de Teams --------------------------------------------


def _archivo(nombre: str, extension: str, url: str = "https://empresa-my.sharepoint.com/f/1") -> dict:
    return {
        "contentType": TIPO_ARCHIVO,
        "name": nombre,
        "content": {"downloadUrl": url, "uniqueId": "1", "fileType": extension},
    }


def _ejecutar(funcion, manejador):
    async def escenario():
        transporte = httpx.MockTransport(manejador)
        async with httpx.AsyncClient(transport=transporte) as cliente:
            return await funcion(cliente)

    return asyncio.run(escenario())


def test_descarga_un_pdf_sin_enviar_el_token() -> None:
    peticiones: list[httpx.Request] = []

    def manejador(peticion: httpx.Request) -> httpx.Response:
        peticiones.append(peticion)
        return httpx.Response(200, content=b"%PDF-1.4 contenido")

    adjuntos = _ejecutar(
        lambda c: descargar_archivos([_archivo("informe.pdf", "pdf")], c), manejador
    )

    assert len(adjuntos) == 1
    assert adjuntos[0].nombre == "informe.pdf"
    assert adjuntos[0].mime == "application/pdf"
    assert "authorization" not in peticiones[0].headers


def test_descarga_word_y_excel_con_su_tipo() -> None:
    def manejador(peticion: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"PK\x03\x04 zip")

    adjuntos = _ejecutar(
        lambda c: descargar_archivos(
            [_archivo("a.docx", "docx"), _archivo("b.xlsx", "xlsx")], c
        ),
        manejador,
    )

    assert [a.mime for a in adjuntos] == [MIME_DOCX, MIME_XLSX]


def test_toma_la_extension_del_nombre_si_falta_filetype() -> None:
    def manejador(peticion: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"%PDF-1.4")

    adjunto = {
        "contentType": TIPO_ARCHIVO,
        "name": "Tarea Final.PDF",
        "content": {"downloadUrl": "https://empresa-my.sharepoint.com/f/1"},
    }

    adjuntos = _ejecutar(lambda c: descargar_archivos([adjunto], c), manejador)

    assert adjuntos[0].mime == "application/pdf"


def test_los_formatos_antiguos_piden_guardar_como_nuevo() -> None:
    def manejador(peticion: httpx.Request) -> httpx.Response:
        raise AssertionError("no deberia descargar nada")

    with pytest.raises(AdjuntoNoSoportadoError, match=r"\.docx"):
        _ejecutar(
            lambda c: descargar_archivos([_archivo("viejo.doc", "doc")], c), manejador
        )


def test_un_tipo_desconocido_se_rechaza_antes_de_descargar() -> None:
    def manejador(peticion: httpx.Request) -> httpx.Response:
        raise AssertionError("no deberia descargar nada")

    with pytest.raises(AdjuntoNoSoportadoError, match="No sé leer"):
        _ejecutar(
            lambda c: descargar_archivos([_archivo("musica.mp3", "mp3")], c), manejador
        )


def test_rechaza_un_pdf_que_no_lo_es() -> None:
    def manejador(peticion: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"<html>no soy un pdf</html>")

    with pytest.raises(AdjuntoNoSoportadoError, match="válido"):
        _ejecutar(
            lambda c: descargar_archivos([_archivo("falso.pdf", "pdf")], c), manejador
        )


def test_rechaza_enlaces_http() -> None:
    def manejador(peticion: httpx.Request) -> httpx.Response:
        raise AssertionError("no deberia descargar nada")

    with pytest.raises(AdjuntoNoSoportadoError, match="seguro"):
        _ejecutar(
            lambda c: descargar_archivos(
                [_archivo("a.pdf", "pdf", url="http://empresa.sharepoint.com/a")], c
            ),
            manejador,
        )


def test_un_error_de_descarga_da_un_mensaje_claro() -> None:
    def manejador(peticion: httpx.Request) -> httpx.Response:
        return httpx.Response(403)

    with pytest.raises(AdjuntoNoSoportadoError, match="No pude descargar"):
        _ejecutar(
            lambda c: descargar_archivos([_archivo("a.pdf", "pdf")], c), manejador
        )


def test_descargar_adjuntos_junta_imagenes_y_archivos() -> None:
    png = b"\x89PNG\r\n\x1a\n" + b"0" * 20

    def manejador(peticion: httpx.Request) -> httpx.Response:
        if peticion.url.host == "login.microsoftonline.com":
            return httpx.Response(200, json={"access_token": "TOKEN"})
        if peticion.url.host == "smba.trafficmanager.net":
            return httpx.Response(200, content=png)
        return httpx.Response(200, content=b"%PDF-1.4")

    attachments = [
        {"contentType": "text/html", "content": "<p>hola</p>"},
        {
            "contentType": "image/*",
            "contentUrl": "https://smba.trafficmanager.net/amer/x/v3/attachments/1/views/original",
        },
        _archivo("informe.pdf", "pdf"),
    ]

    adjuntos = _ejecutar(
        lambda c: descargar_adjuntos(attachments, CONFIG, c), manejador
    )

    assert [a.mime for a in adjuntos] == ["image/png", "application/pdf"]
