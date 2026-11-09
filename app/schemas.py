"""Contrato HTTP. Los nombres en camelCase son los del mentor del ai-service,
para que el backend (`ClienteServicioIa.preguntarAlMentor`) apunte aqui sin cambios."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

MAX_PREGUNTA = 500
MAX_RECIENTES = 3
MAX_PERFIL = 12


class _Base(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel, populate_by_name=True, extra="ignore", str_strip_whitespace=True
    )


class CriterioDelPerfil(_Base):
    nombre: str = Field(min_length=1, max_length=120)
    porcentaje: float = Field(ge=0, le=100)
    veces: int = Field(ge=1, le=10_000)


class Flojo(_Base):
    criterio: str = Field(min_length=1, max_length=120)
    porcentaje: float = Field(ge=0, le=100)
    evidencia: str = Field(max_length=2000)


class EvaluacionReciente(_Base):
    reto: str = Field(min_length=1, max_length=200)
    nota: float = Field(ge=0, le=100)
    flojo: Flojo | None = None


class Contexto(_Base):
    total_evaluaciones: int = Field(ge=0, le=100_000)
    promedio: float = Field(ge=0, le=100)
    perfil: list[CriterioDelPerfil] = Field(max_length=MAX_PERFIL)
    recientes: list[EvaluacionReciente] = Field(max_length=MAX_RECIENTES)


class Turno(_Base):
    rol: Literal["candidato", "mentor"]
    texto: str = Field(max_length=4000)


class SolicitudDeMentor(_Base):
    contexto: Contexto
    historial: list[Turno] = Field(max_length=50)
    pregunta: str = Field(min_length=1, max_length=MAX_PREGUNTA)


class Fuente(_Base):
    """De donde salio lo que dice el mentor: para que el candidato (y el equipo) lo verifiquen."""

    n: int  # el [n] con que la respuesta lo cita
    id: str
    titulo: str
    archivo: str
    extracto: str
    puntaje: float
    rango_lexico: int | None
    rango_semantico: int | None


class RespuestaDeMentor(_Base):
    respuesta: str
    sugerencias: list[str]
    fuentes: list[Fuente]
    proveedor: str
    modelo: str
    vectorizador: str


class RespuestaDeBusqueda(_Base):
    consulta: str
    resultados: list[Fuente]
