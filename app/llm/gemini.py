"""Adaptador de Gemini. Todo lo especifico del SDK y sus errores vive aqui."""

from __future__ import annotations

import asyncio

from google import genai
from google.genai import errors, types

from .base import (
    ProveedorNoDisponibleError,
    ProveedorRechazoLaSolicitudError,
    SolicitudAlModelo,
)

_BLOQUEOS = {"SAFETY", "RECITATION", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "LANGUAGE"}


class GeneradorGemini:
    nombre = "gemini"

    def __init__(self, api_key: str, modelo: str, tiempo_maximo_ms: int) -> None:
        self.modelo = modelo
        self._tiempo_s = tiempo_maximo_ms / 1000
        self._cliente = genai.Client(api_key=api_key)

    async def generar_json(self, s: SolicitudAlModelo) -> str:
        try:
            r = await asyncio.wait_for(
                self._cliente.aio.models.generate_content(
                    model=self.modelo,
                    contents=s.contenido,
                    config=types.GenerateContentConfig(
                        system_instruction=s.instruccion_de_sistema,
                        response_mime_type="application/json",
                        response_json_schema=s.esquema,
                        temperature=s.temperatura,
                        max_output_tokens=s.max_tokens,
                    ),
                ),
                timeout=self._tiempo_s,
            )
        except asyncio.TimeoutError as e:
            raise ProveedorNoDisponibleError("El proveedor no respondio a tiempo.") from e
        except errors.APIError as e:
            code = getattr(e, "code", 0) or 0
            if code in (408, 429) or code >= 500:
                raise ProveedorNoDisponibleError(f"Gemini {code}.") from e
            raise ProveedorRechazoLaSolicitudError(f"Gemini rechazo la solicitud ({code}).") from e
        except OSError as e:  # red
            raise ProveedorNoDisponibleError("Fallo de red hacia Gemini.") from e

        if r.prompt_feedback and r.prompt_feedback.block_reason:
            raise ProveedorRechazoLaSolicitudError("Gemini bloqueo la solicitud.")
        cand = (r.candidates or [None])[0]
        if cand and cand.finish_reason and str(cand.finish_reason.name) in _BLOQUEOS:
            raise ProveedorRechazoLaSolicitudError(f"Gemini detuvo la respuesta ({cand.finish_reason.name}).")
        return r.text or ""
