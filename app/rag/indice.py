"""Corpus -> fragmentos -> indice hibrido (BM25 + vectores) con cache en disco."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .bm25 import BM25
from .embeddings import Vectorizador
from .fusion import Fusionado, fusionar_rrf
from .texto import tokenizar

MAX_CARACTERES_POR_FRAGMENTO = 900


@dataclass(frozen=True)
class Fragmento:
    id: str  # "<archivo>#<n>", estable mientras no cambie el archivo
    fuente: str  # nombre del archivo
    titulo: str  # "Documento > Seccion"
    texto: str

    @property
    def para_indexar(self) -> str:
        # El titulo entra en el indice: "Complejidad > Errores comunes" aporta
        # terminos que el cuerpo del parrafo puede no repetir.
        return f"{self.titulo}\n{self.texto}"


@dataclass(frozen=True)
class Resultado:
    fragmento: Fragmento
    puntaje: float
    rango_lexico: int | None
    rango_semantico: int | None


def trocear(fuente: str, markdown: str) -> list[Fragmento]:
    """Un fragmento por seccion `##`; las secciones largas se parten por parrafos."""
    h1 = re.search(r"^# (.+)$", markdown, re.M)
    doc = h1.group(1).strip() if h1 else fuente
    partes = re.split(r"^## +(.+)$", markdown, flags=re.M)
    # partes = [preambulo, titulo1, cuerpo1, titulo2, cuerpo2, ...]
    secciones = [(doc, re.sub(r"^# .+$", "", partes[0], flags=re.M))] + [
        (f"{doc} > {partes[i].strip()}", partes[i + 1]) for i in range(1, len(partes) - 1, 2)
    ]
    salida: list[Fragmento] = []
    for titulo, cuerpo in secciones:
        bloques, actual = [], ""
        for p in re.split(r"\n\s*\n", cuerpo.strip()):
            if actual and len(actual) + len(p) > MAX_CARACTERES_POR_FRAGMENTO:
                bloques.append(actual)
                actual = ""
            actual = f"{actual}\n\n{p}".strip()
        if actual:
            bloques.append(actual)
        for b in bloques:
            salida.append(Fragmento(f"{fuente}#{len(salida) + 1}", fuente, titulo, b))
    return salida


def cargar_corpus(directorio: Path) -> list[Fragmento]:
    fragmentos: list[Fragmento] = []
    for ruta in sorted(directorio.glob("*.md")):
        fragmentos.extend(trocear(ruta.name, ruta.read_text(encoding="utf-8")))
    if not fragmentos:
        raise RuntimeError(f"No hay archivos .md con contenido en {directorio}.")
    return fragmentos


class IndiceHibrido:
    def __init__(
        self,
        fragmentos: list[Fragmento],
        vectorizador: Vectorizador,
        *,
        dir_cache: Path | None = None,
        k_candidatos: int = 20,
        rrf_k: int = 60,
        peso_lexico: float = 1.0,
        peso_semantico: float = 1.0,
    ) -> None:
        self.fragmentos = fragmentos
        self._vectorizador = vectorizador
        self._k_candidatos, self._rrf_k = k_candidatos, rrf_k
        self._pesos = (peso_lexico, peso_semantico)
        self._bm25 = BM25([tokenizar(f.para_indexar) for f in fragmentos])
        self._vectores = self._cargar_o_calcular(dir_cache)

    @property
    def nombre_vectorizador(self) -> str:
        return self._vectorizador.nombre

    def _cargar_o_calcular(self, dir_cache: Path | None) -> np.ndarray:
        textos = [f.para_indexar for f in self.fragmentos]
        # La clave incluye el modelo: cambiar de vectorizador no puede reutilizar vectores ajenos.
        huella = hashlib.sha256(
            "\x00".join([self._vectorizador.nombre, *textos]).encode()
        ).hexdigest()[:20]
        ruta = dir_cache / f"vectores-{huella}.npy" if dir_cache else None
        if ruta and ruta.exists():
            return np.load(ruta)
        v = self._vectorizador.vectorizar(textos, "documento")
        if ruta:
            ruta.parent.mkdir(parents=True, exist_ok=True)
            np.save(ruta, v)
        return v

    def buscar(self, consulta: str, k: int = 4) -> list[Resultado]:
        lexico = [i for i, _ in self._bm25.buscar(tokenizar(consulta), self._k_candidatos)]
        q = self._vectorizador.vectorizar([consulta], "consulta")[0]
        sims = self._vectores @ q
        semantico = [int(i) for i in np.argsort(-sims, kind="stable")[: self._k_candidatos]]
        fusion: list[Fusionado] = fusionar_rrf(
            lexico,
            semantico,
            k=self._rrf_k,
            peso_lexico=self._pesos[0],
            peso_semantico=self._pesos[1],
        )
        return [
            Resultado(self.fragmentos[f.indice], f.puntaje, f.rango_lexico, f.rango_semantico)
            for f in fusion[:k]
        ]
