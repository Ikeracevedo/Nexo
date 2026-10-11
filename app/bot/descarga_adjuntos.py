"""Descarga de adjuntos desde Teams: imagenes y archivos (PDF, Word, Excel).

Vive en app/bot porque saber como entrega Teams los archivos es asunto
del canal: el nucleo solo recibe objetos Adjunto ya descargados.

Teams entrega dos clases de adjunto:

- Imagen pegada en el chat: contentType "image/*" y un contentUrl que exige
  el token del bot (Authorization: Bearer). Ese token se pide con las
  credenciales del bot (client credentials).
- Archivo subido con el clip: contentType
  "application/vnd.microsoft.teams.file.download.info", con una URL de
  descarga que YA viene autorizada (downloadUrl). Esa se baja sin token.
"""

from __future__ import annotations

import json
import logging
from collections.abc import Iterable
from typing import Any
from urllib.parse import urlparse

import httpx

from app.config import Configuracion
from app.dominio.adjunto import (
    MAX_BYTES_ADJUNTO,
    MIME_DOCX,
    MIME_XLSX,
    Adjunto,
    AdjuntoNoSoportadoError,
)

logger = logging.getLogger(__name__)

_AMBITO_BOT = "https://api.botframework.com/.default"

# El token del bot solo se envia a estos dominios, nunca a una URL cualquiera
# que venga dentro de un mensaje.
_HOSTS_CONFIABLES = ("trafficmanager.net", "botframework.com", "skype.com")

_EXTENSIONES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "image/gif": "gif",
}

MAX_IMAGENES = 4

# --- Archivos subidos con el clip -----------------------------------------

_TIPO_ARCHIVO_TEAMS = "application/vnd.microsoft.teams.file.download.info"

_MIME_POR_EXTENSION = {
    "pdf": "application/pdf",
    "docx": MIME_DOCX,
    "xlsx": MIME_XLSX,
}

# Los .docx y .xlsx son zips (empiezan por "PK"); los PDF por "%PDF".
_FIRMAS = {
    "pdf": b"%PDF",
    "docx": b"PK\x03\x04",
    "xlsx": b"PK\x03\x04",
}

_FORMATOS_ANTIGUOS = {"doc": "docx", "xls": "xlsx"}

MAX_ARCHIVOS = 3


def _campo(adjunto: Any, *nombres: str) -> Any:
    """Lee un campo aceptando snake_case, camelCase, objetos o diccionarios."""
    for nombre in nombres:
        valor = getattr(adjunto, nombre, None)
        if valor is None and isinstance(adjunto, dict):
            valor = adjunto.get(nombre)
        if valor is not None:
            return valor
    return None


def _tipo(adjunto: Any) -> str:
    return _campo(adjunto, "content_type", "contentType") or ""


def _urls_de_imagenes(attachments: Iterable[Any]) -> list[str]:
    urls: list[str] = []
    for adjunto in attachments:
        url = _campo(adjunto, "content_url", "contentUrl")
        if _tipo(adjunto).startswith("image/") and url:
            urls.append(url)
    return urls[:MAX_IMAGENES]


def _host_confiable(host: str) -> bool:
    return any(host == d or host.endswith("." + d) for d in _HOSTS_CONFIABLES)


def _detectar_mime(datos: bytes) -> str | None:
    """Reconoce el formato por los primeros bytes. Teams manda 'image/*'
    y los servidores a veces responden octet-stream, asi que no sirven."""
    if datos.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if datos.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if datos.startswith((b"GIF87a", b"GIF89a")):
        return "image/gif"
    if datos[:4] == b"RIFF" and datos[8:12] == b"WEBP":
        return "image/webp"
    return None


async def _token_del_bot(config: Configuracion, cliente: httpx.AsyncClient) -> str:
    tenant = config.azure_tenant_id or "botframework.com"
    try:
        respuesta = await cliente.post(
            f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token",
            data={
                "grant_type": "client_credentials",
                "client_id": config.teams_bot_id,
                "client_secret": config.teams_bot_password,
                "scope": _AMBITO_BOT,
            },
        )
        respuesta.raise_for_status()
        return respuesta.json()["access_token"]
    except (httpx.HTTPError, KeyError, ValueError) as error:
        logger.warning("No se pudo obtener el token del bot: %s", type(error).__name__)
        raise AdjuntoNoSoportadoError(
            "No pude autenticarme para descargar el archivo."
        ) from error


async def _bajar(url: str, token: str | None, cliente: httpx.AsyncClient) -> bytes:
    cabeceras = {"Authorization": f"Bearer {token}"} if token else {}
    datos = bytearray()
    async with cliente.stream(
        "GET", url, headers=cabeceras, follow_redirects=True
    ) as respuesta:
        respuesta.raise_for_status()
        async for trozo in respuesta.aiter_bytes():
            datos.extend(trozo)
            if len(datos) > MAX_BYTES_ADJUNTO:
                limite = MAX_BYTES_ADJUNTO // (1024 * 1024)
                raise AdjuntoNoSoportadoError(f"El archivo pesa más de {limite} MB.")
    return bytes(datos)


# --- Imagenes --------------------------------------------------------------


async def _descargar_imagenes(
    urls: list[str],
    config: Configuracion,
    cliente: httpx.AsyncClient,
) -> list[Adjunto]:
    adjuntos: list[Adjunto] = []
    token: str | None = None

    for posicion, url in enumerate(urls):
        partes = urlparse(url)
        if partes.scheme != "https":
            raise AdjuntoNoSoportadoError(
                "No puedo descargar esa imagen: el enlace no es seguro."
            )

        usar_token = _host_confiable(partes.hostname or "")
        if usar_token and token is None:
            token = await _token_del_bot(config, cliente)

        try:
            datos = await _bajar(url, token if usar_token else None, cliente)
        except httpx.HTTPError as error:
            estado = getattr(getattr(error, "response", None), "status_code", "?")
            logger.warning(
                "Fallo la descarga de la imagen (estado %s, host %s)",
                estado,
                partes.hostname,
            )
            raise AdjuntoNoSoportadoError(
                "No pude descargar la imagen. Intenta enviarla otra vez."
            ) from error

        mime = _detectar_mime(datos)
        if mime is None:
            raise AdjuntoNoSoportadoError(
                "No reconocí el formato de la imagen. Puedo leer PNG, JPG, WEBP y GIF."
            )

        base = "imagen" if posicion == 0 else f"imagen_{posicion + 1}"
        adjuntos.append(Adjunto(f"{base}.{_EXTENSIONES[mime]}", mime, datos))

    return adjuntos


async def descargar_imagenes(
    attachments: Iterable[Any],
    config: Configuracion,
    cliente: httpx.AsyncClient | None = None,
) -> list[Adjunto]:
    """Descarga las imagenes de la actividad y las devuelve como Adjunto.

    Ignora los adjuntos que no son imagen (el HTML del mensaje, por ejemplo).
    Lanza AdjuntoNoSoportadoError con un mensaje apto para el usuario.
    """
    urls = _urls_de_imagenes(attachments)
    if not urls:
        return []

    if cliente is not None:
        return await _descargar_imagenes(urls, config, cliente)

    async with httpx.AsyncClient(timeout=20) as propio:
        return await _descargar_imagenes(urls, config, propio)


# --- Archivos (PDF, Word, Excel) --------------------------------------------


def _contenido(adjunto: Any) -> Any:
    contenido = _campo(adjunto, "content")
    if isinstance(contenido, str):
        try:
            return json.loads(contenido)
        except ValueError:
            return None
    return contenido


def _archivos_de_teams(attachments: Iterable[Any]) -> list[tuple[str, str, str]]:
    """Devuelve (nombre, extension, url) de cada archivo valido.

    Falla con un mensaje claro si el tipo no se soporta, ANTES de descargar.
    """
    archivos: list[tuple[str, str, str]] = []

    for adjunto in attachments:
        if _tipo(adjunto) != _TIPO_ARCHIVO_TEAMS:
            continue

        contenido = _contenido(adjunto)
        url = _campo(contenido, "download_url", "downloadUrl") if contenido else None
        nombre = _campo(adjunto, "name") or ""
        extension = str(
            (_campo(contenido, "file_type", "fileType") if contenido else None)
            or (nombre.rsplit(".", 1)[-1] if "." in nombre else "")
        ).lower()

        if not url:
            continue

        if extension in _FORMATOS_ANTIGUOS:
            moderno = _FORMATOS_ANTIGUOS[extension]
            raise AdjuntoNoSoportadoError(
                f"«{nombre or 'El archivo'}» está en un formato antiguo (.{extension}). "
                f"Guárdalo como .{moderno} y envíalo otra vez."
            )

        if extension not in _MIME_POR_EXTENSION:
            raise AdjuntoNoSoportadoError(
                f"No sé leer archivos .{extension or 'desconocidos'}. "
                "Puedo leer imágenes, PDF, Word (.docx) y Excel (.xlsx)."
            )

        archivos.append((nombre or f"archivo.{extension}", extension, url))

    return archivos[:MAX_ARCHIVOS]


async def _descargar_archivos(
    archivos: list[tuple[str, str, str]],
    cliente: httpx.AsyncClient,
) -> list[Adjunto]:
    adjuntos: list[Adjunto] = []

    for nombre, extension, url in archivos:
        partes = urlparse(url)
        if partes.scheme != "https":
            raise AdjuntoNoSoportadoError(
                "No puedo descargar ese archivo: el enlace no es seguro."
            )

        try:
            # La URL de descarga ya viene autorizada: NO se envia el token del bot.
            datos = await _bajar(url, None, cliente)
        except httpx.HTTPError as error:
            estado = getattr(getattr(error, "response", None), "status_code", "?")
            logger.warning(
                "Fallo la descarga del archivo (estado %s, host %s)",
                estado,
                partes.hostname,
            )
            raise AdjuntoNoSoportadoError(
                f"No pude descargar «{nombre}». Intenta enviarlo otra vez."
            ) from error

        if not datos.startswith(_FIRMAS[extension]):
            raise AdjuntoNoSoportadoError(
                f"«{nombre}» no parece un archivo .{extension} válido."
            )

        adjuntos.append(Adjunto(nombre, _MIME_POR_EXTENSION[extension], datos))

    return adjuntos


async def descargar_archivos(
    attachments: Iterable[Any],
    cliente: httpx.AsyncClient | None = None,
) -> list[Adjunto]:
    """Descarga los archivos (PDF, Word, Excel) subidos con el clip."""
    archivos = _archivos_de_teams(attachments)
    if not archivos:
        return []

    if cliente is not None:
        return await _descargar_archivos(archivos, cliente)

    async with httpx.AsyncClient(timeout=30) as propio:
        return await _descargar_archivos(archivos, propio)


# --- Punto de entrada para el bot ---------------------------------------------


async def descargar_adjuntos(
    attachments: Iterable[Any],
    config: Configuracion,
    cliente: httpx.AsyncClient | None = None,
) -> list[Adjunto]:
    """Descarga todo lo que el nucleo sabe leer: imagenes y archivos."""
    lista = list(attachments)

    # Solo tipos y cantidad, nunca URLs. Sirve para depurar que llega.
    logger.info("Tipos de adjuntos recibidos: %s", [_tipo(a) for a in lista])

    imagenes = await descargar_imagenes(lista, config, cliente)
    archivos = await descargar_archivos(lista, cliente)
    return [*imagenes, *archivos]
