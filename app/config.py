"""Configuracion del servicio, leida del entorno (ver .env.example)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

RAIZ = Path(__file__).resolve().parent.parent


class Ajustes(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_env: Literal["development", "test", "production"] = "development"
    port: int = 3200

    # Secreto compartido con el backend (alli: AI_SERVICE_API_KEY).
    clave_de_acceso: str = Field(min_length=32)

    # Modelo que redacta la respuesta. `simulado` no llama a nadie.
    proveedor_ia: Literal["gemini", "simulado"] = "gemini"
    # Modelo que vectoriza. `hash` es local y sin red (solo desarrollo y pruebas).
    embeddings: Literal["gemini", "hash"] = "gemini"

    gemini_api_key: str = ""
    gemini_modelo: str = "gemini-3.5-flash"
    gemini_modelo_embeddings: str = "gemini-embedding-001"
    embeddings_dimension: int = 768

    tiempo_maximo_ms: int = 30_000

    dir_conocimiento: Path = RAIZ / "conocimiento"
    dir_cache: Path = RAIZ / ".cache"

    # Recuperacion hibrida.
    k_candidatos: int = 20  # cuantos trae cada recuperador antes de fusionar
    k_final: int = 4  # cuantos fragmentos llegan al modelo
    peso_lexico: float = 1.0
    peso_semantico: float = 1.0
    rrf_k: int = 60

    @model_validator(mode="after")
    def _validar(self) -> "Ajustes":
        if self.app_env == "production" and (
            self.proveedor_ia == "simulado" or self.embeddings == "hash"
        ):
            raise ValueError("PROVEEDOR_IA=simulado y EMBEDDINGS=hash estan prohibidos en produccion.")
        if "gemini" in (self.proveedor_ia, self.embeddings) and not self.gemini_api_key:
            raise ValueError("Falta GEMINI_API_KEY (o usa PROVEEDOR_IA=simulado y EMBEDDINGS=hash).")
        return self


@lru_cache
def obtener_ajustes() -> Ajustes:
    return Ajustes()  # type: ignore[call-arg]
