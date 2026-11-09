"""Interfaz de proveedor de generacion, y los errores que el resto del servicio entiende."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


class ProveedorNoDisponibleError(Exception):
    """Caida, sobrecarga (429/5xx), red o tiempo agotado. Reintentable."""


class ProveedorRechazoLaSolicitudError(Exception):
    """Clave invalida, modelo inexistente, contenido bloqueado. Repetir no cambia nada."""


class SalidaInvalidaError(Exception):
    """El modelo respondio algo que no cumple el contrato. Reintentable."""


@dataclass(frozen=True)
class SolicitudAlModelo:
    instruccion_de_sistema: str
    contenido: str
    esquema: dict[str, Any]
    max_tokens: int
    temperatura: float
    # Solo para el simulado, que no entiende `contenido`: los textos recuperados.
    pistas: tuple[str, ...] = field(default=())


class Generador(Protocol):
    nombre: str
    modelo: str

    async def generar_json(self, s: SolicitudAlModelo) -> str:
        """Texto crudo del modelo. NO se interpreta aqui: validarlo es del dominio."""
        ...
