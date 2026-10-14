from __future__ import annotations

import re
from functools import lru_cache
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Validador de campos de la las variables de entorno que deben ser GUID. Se usa en Configuracion.
_GUID = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")


class Configuracion(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    brujula_entorno: str = "local"
    brujula_log_level: str = "INFO"
    brujula_zona_horaria: str = "America/Bogota"

    # Marca del asistente. Todo texto que el usuario lee (ayuda, tarjetas,
    # prompts) sale de aqui: renombrarlo es una variable, no un commit.
    bot_nombre: str = "Nexo"

    azure_tenant_id: str = ""
    azure_client_id: str = ""
    azure_client_secret: str = ""
    azure_redirect_uri: str = "http://localhost:8000/auth/callback"

    # Credenciales del registro de bot (Bot Framework / Azure Bot).
    # Distintas del registro de Entra ID para Graph: son dos identidades.
    teams_bot_id: str = ""
    teams_bot_password: str = ""
    teams_oauth_connection: str = "graph"

    gemini_api_key: str = ""
    # El modelo sale de configuracion, no del codigo: cambiarlo es
    # exactamente lo que el ADR-006 queria que costara una variable.
    gemini_modelo: str = "gemini-2.5-flash"
    mongodb_uri: str = ""
    brujula_url_publica: str = "https://brujula-teams.duckdns.org"
    brujula_token_encryption_key: str = ""

    @field_validator("azure_tenant_id", "azure_client_id", "teams_bot_id")
    @classmethod
    def _debe_ser_guid_si_tiene_valor(cls, v: str, info: ValidationInfo) -> str:
        """
        Mismo principio que Pendiente.__post_init__: si un valor invalido
        no puede existir, no hay que acordarse de comprobarlo mas tarde.
        Vacio se acepta: significa "todavia no configurado".
        """
        v = v.strip()
        if v and not _GUID.match(v):
            raise ValueError(
                f"{info.field_name} no tiene forma de GUID ({len(v)} caracteres; "
                f"un GUID tiene 36). Revisa que lo copiaste completo desde el portal."
            )
        return v

    @field_validator("brujula_zona_horaria")
    @classmethod
    def _debe_ser_zona_iana(cls, v: str) -> str:
        try:
            ZoneInfo(v)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError(f"brujula_zona_horaria '{v}' no es una zona IANA valida") from error
        return v


@lru_cache
def obtener_configuracion() -> Configuracion:
    """Devuelve la configuracion, leida del entorno una sola vez.

    lru_cache la convierte en singleton: el .env se lee en la primera
    llamada y se reutiliza despues. En los tests se limpia con
    obtener_configuracion.cache_clear().
    """
    return Configuracion()
