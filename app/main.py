"""API HTTP. Mismo formato de errores y misma autenticacion que el ai-service."""

from __future__ import annotations

import logging
import secrets
import uuid
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .config import Ajustes, obtener_ajustes
from .llm.base import (
    Generador,
    ProveedorNoDisponibleError,
    ProveedorRechazoLaSolicitudError,
    SalidaInvalidaError,
)
from .mentor import MentorRag, a_fuente
from .rag.embeddings import Vectorizador, VectorizadorGemini, VectorizadorHash
from .rag.indice import IndiceHibrido, cargar_corpus
from .schemas import RespuestaDeBusqueda, RespuestaDeMentor, SolicitudDeMentor

logging.basicConfig(level=logging.INFO, format="%(message)s")


def crear_vectorizador(a: Ajustes) -> Vectorizador:
    if a.embeddings == "hash":
        return VectorizadorHash()
    return VectorizadorGemini(
        a.gemini_api_key, a.gemini_modelo_embeddings, a.embeddings_dimension, a.tiempo_maximo_ms
    )


def crear_generador(a: Ajustes) -> Generador:
    if a.proveedor_ia == "simulado":
        from .llm.simulado import GeneradorSimulado

        return GeneradorSimulado()
    from .llm.gemini import GeneradorGemini

    return GeneradorGemini(a.gemini_api_key, a.gemini_modelo, a.tiempo_maximo_ms)


def construir_mentor(a: Ajustes, vectorizador: Vectorizador | None = None, generador: Generador | None = None) -> MentorRag:
    indice = IndiceHibrido(
        cargar_corpus(a.dir_conocimiento),
        vectorizador or crear_vectorizador(a),
        dir_cache=a.dir_cache,
        k_candidatos=a.k_candidatos,
        rrf_k=a.rrf_k,
        peso_lexico=a.peso_lexico,
        peso_semantico=a.peso_semantico,
    )
    return MentorRag(indice, generador or crear_generador(a), k_final=a.k_final)


def crear_app(mentor: MentorRag | None = None, ajustes: Ajustes | None = None) -> FastAPI:
    a = ajustes or obtener_ajustes()

    @asynccontextmanager
    async def ciclo(app: FastAPI):
        app.state.mentor = mentor or construir_mentor(a)  # indexa al arrancar, no en la 1a peticion
        yield

    # Sin /docs en produccion: igual que el ai-service.
    app = FastAPI(
        title="MeritIA · Mentor RAG",
        version="0.1.0",
        lifespan=ciclo,
        docs_url=None if a.app_env == "production" else "/api/docs",
        redoc_url=None,
    )

    def autenticar(authorization: Annotated[str | None, Header()] = None) -> None:
        esperado = f"Bearer {a.clave_de_acceso}"
        # compare_digest: no filtra por tiempo cuantos caracteres acerto.
        if not authorization or not secrets.compare_digest(authorization.encode(), esperado.encode()):
            raise HTTPException(401, detail="NO_AUTENTICADO")

    def error(status: int, codigo: str, mensaje: str, reintentable: bool, **extra: object) -> JSONResponse:
        return JSONResponse(
            status_code=status,
            content={"codigo": codigo, "mensaje": mensaje, "reintentable": reintentable, **extra},
        )

    @app.exception_handler(HTTPException)
    async def _http(_: Request, e: HTTPException):
        if e.status_code == 401:
            return error(401, "NO_AUTENTICADO", "Falta la clave de acceso o no es valida.", False)
        return error(e.status_code, "HTTP", str(e.detail), False)

    @app.exception_handler(RequestValidationError)
    async def _validacion(_: Request, e: RequestValidationError):
        # Solo donde falla, nunca el valor: la pregunta es texto del candidato.
        campos = [".".join(map(str, x["loc"][1:])) for x in e.errors()]
        return error(400, "VALIDACION", "La peticion no cumple el contrato.", False, campos=campos)

    @app.exception_handler(ProveedorNoDisponibleError)
    async def _no_disponible(_: Request, __: ProveedorNoDisponibleError):
        return error(503, "PROVEEDOR_NO_DISPONIBLE", "El proveedor de IA no esta disponible.", True)

    @app.exception_handler(ProveedorRechazoLaSolicitudError)
    async def _rechazo(_: Request, __: ProveedorRechazoLaSolicitudError):
        return error(422, "SOLICITUD_RECHAZADA_POR_PROVEEDOR", "El proveedor rechazo la solicitud.", False)

    @app.exception_handler(SalidaInvalidaError)
    async def _salida(_: Request, __: SalidaInvalidaError):
        return error(502, "SALIDA_INVALIDA", "El modelo respondio algo fuera del contrato.", True)

    @app.exception_handler(Exception)
    async def _interno(_: Request, e: Exception):
        ref = uuid.uuid4().hex[:12]
        logging.getLogger("rag").error("interno ref=%s %s", ref, type(e).__name__, exc_info=e)
        return error(500, "INTERNO", "Error interno.", False, referencia=ref)

    @app.get("/api/v1/salud")
    async def salud() -> dict[str, object]:
        return {"estado": "ok", "fragmentos": app.state.mentor.total_fragmentos}

    @app.post("/api/v1/mentor", response_model=RespuestaDeMentor, response_model_by_alias=True,
              dependencies=[Depends(autenticar)])
    async def mentor_endpoint(s: SolicitudDeMentor) -> RespuestaDeMentor:
        return await app.state.mentor.responder(s)

    @app.get("/api/v1/conocimiento/buscar", response_model=RespuestaDeBusqueda,
             response_model_by_alias=True, dependencies=[Depends(autenticar)])
    async def buscar(q: Annotated[str, Query(min_length=1, max_length=500)]) -> RespuestaDeBusqueda:
        """Muestra que recupera el indice hibrido para una consulta, sin llamar al modelo."""
        r = await app.state.mentor.recuperar(q)
        return RespuestaDeBusqueda(consulta=q, resultados=[a_fuente(i, x) for i, x in enumerate(r, 1)])

    return app


def app_por_omision() -> FastAPI:  # uvicorn --factory app.main:app_por_omision
    return crear_app()
