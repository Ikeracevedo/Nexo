"""Caso de uso: el usuario le dicta un pendiente a Nexo.

Responsabilidades de este servicio:
  1. Extraer el titulo de la peticion ("recuerdame entregar el informe el viernes")
  2. Interpretar la fecha de forma determinista (sin LLM)
  3. Delegar el almacenamiento al puerto PendientesRepository

Por que sin LLM para la fecha: un parseo determinista de cuatro casos
(hoy, manana, dia de semana, DD/MM) es testeable, gratuito e instantaneo.
El LLM entra cuando el problema es abierto; una fecha no lo es.
Si un `if` resuelve el caso, un modelo es la respuesta cara y menos fiable.

Por que en un servicio y no en el handler del bot: la Capa de Bot Delgada
(ADR-001) exige que el handler solo traduzca, no decida. Todo lo que queda
dentro de un handler es imposible de testear sin Teams conectado. Todo lo
que sale de el se prueba en 20 milisegundos.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, time, timedelta

from app.dominio.pendiente import Pendiente
from app.puertos.pendientes_repository import PendientesRepository

_DIAS_ES: dict[str, int] = {
    "lunes": 0,
    "martes": 1,
    "miercoles": 2,
    "miércoles": 2,
    "jueves": 3,
    "viernes": 4,
    "sabado": 5,
    "sábado": 5,
    "domingo": 6,
}

_PAT_PREFIJO = re.compile(r"^\s*rec[uú][eé]rdame\s*", re.IGNORECASE)
_PAT_HOY = re.compile(r"(?:^|\s+)hoy\s*$", re.IGNORECASE)
_PAT_MANANA = re.compile(r"(?:^|\s+)ma[ñn]ana\s*$", re.IGNORECASE)
_PAT_DIA_SEMANA = re.compile(
    # (?:^|\s+): dia puede ser el unico contenido ("el viernes") o ir al
    # final del titulo ("entregar el informe el viernes"). El titulo vacio
    # resultante se rechaza en recordar() con ValueError.
    r"(?:^|\s+)(?:el|este)\s+"
    r"(?P<dia>lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)"
    r"\s*$",
    re.IGNORECASE,
)
_PAT_FECHA_NUMERICA = re.compile(
    r"\s+el\s+(?P<d>\d{1,2})/(?P<m>\d{1,2})(?:/(?P<a>\d{2,4}))?\s*$",
    re.IGNORECASE,
)


def _extraer_titulo_y_fecha(texto_sin_prefijo: str, ahora: date) -> tuple[str, date | None]:
    """Separa titulo de indicador de fecha. Busca el indicador al final del texto.

    Buscar al final minimiza falsos positivos: "entregar el informe el viernes"
    reconoce "el viernes" como fecha sin tocar "el informe".
    """
    texto = texto_sin_prefijo.strip()

    if m := _PAT_FECHA_NUMERICA.search(texto):
        d, mes = int(m.group("d")), int(m.group("m"))
        a_raw = m.group("a")
        anio = int(a_raw) if a_raw else ahora.year
        if anio < 100:
            anio += 2000
        try:
            fecha = date(anio, mes, d)
            return _PAT_FECHA_NUMERICA.sub("", texto).strip(), fecha
        except ValueError:
            pass  # Fecha invalida (ej. 31/02); se trata como sin fecha

    if _PAT_MANANA.search(texto):
        return _PAT_MANANA.sub("", texto).strip(), ahora + timedelta(days=1)

    if _PAT_HOY.search(texto):
        return _PAT_HOY.sub("", texto).strip(), ahora

    if m := _PAT_DIA_SEMANA.search(texto):
        dia_nombre = m.group("dia").lower().replace("é", "e").replace("á", "a")
        dia_num = _DIAS_ES.get(dia_nombre, -1)
        if dia_num >= 0:
            dias_hasta = (dia_num - ahora.weekday()) % 7
            if dias_hasta == 0:
                dias_hasta = 7  # Si es hoy el mismo dia, va a la semana siguiente
            return _PAT_DIA_SEMANA.sub("", texto).strip(), ahora + timedelta(days=dias_hasta)

    return texto, None


class ServicioPendientesPropios:
    """Interpreta 'recuerdame ...' y persiste el pendiente via el repositorio."""

    def __init__(self, repositorio: PendientesRepository) -> None:
        self._repo = repositorio

    async def recordar(self, texto: str, usuario_id: str, ahora: datetime) -> Pendiente:
        """Parsea el texto, extrae titulo y fecha, guarda via el repositorio.

        Raises:
            ValueError: si no se pudo extraer un titulo valido del texto.
        """
        texto_sin_prefijo = _PAT_PREFIJO.sub("", texto).strip()
        titulo, fecha = _extraer_titulo_y_fecha(texto_sin_prefijo, ahora.date())

        if not titulo:
            raise ValueError(
                "No encontre el titulo del pendiente. "
                'Ejemplo: "recuerdame entregar el informe el viernes"'
            )

        vence = datetime.combine(fecha, time(0, 0), tzinfo=UTC) if fecha else None
        return await self._repo.guardar(usuario_id, titulo, vence)

    async def completar(self, pendiente_id: str, usuario_id: str) -> bool:
        """Marca un pendiente propio como completado."""
        return await self._repo.completar(pendiente_id, usuario_id)

    async def borrar(self, pendiente_id: str, usuario_id: str) -> bool:
        """Borra definitivamente un pendiente propio."""
        return await self._repo.borrar(pendiente_id, usuario_id)
