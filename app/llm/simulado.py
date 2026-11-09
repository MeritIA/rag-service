"""Generador sin modelo: responde con el mejor fragmento recuperado, tal cual.

Sirve para desarrollar y probar la recuperacion sin API key, y deja a la vista
que se recupero (la respuesta ES el fragmento). Prohibido en produccion.
"""

from __future__ import annotations

import json

from .base import SolicitudAlModelo


class GeneradorSimulado:
    nombre = "simulado"
    modelo = "extractivo"

    async def generar_json(self, s: SolicitudAlModelo) -> str:
        if not s.pistas:
            return json.dumps(
                {"respuesta": "[simulado] No encontre material relacionado.", "sugerencias": [], "usadas": []}
            )
        return json.dumps(
            {
                "respuesta": f"[simulado] {s.pistas[0]}",
                "sugerencias": [],
                "usadas": list(range(1, len(s.pistas) + 1)),
            }
        )
