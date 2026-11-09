from pathlib import Path

import pytest

from app.config import RAIZ
from app.rag.bm25 import BM25
from app.rag.embeddings import VectorizadorHash
from app.rag.fusion import fusionar_rrf
from app.rag.indice import IndiceHibrido, cargar_corpus, trocear
from app.rag.texto import condensar, tokenizar


def test_tokenizar_ignora_acentos_mayusculas_y_stopwords():
    assert tokenizar("La Complejidad ALGORÍTMICA de los datos") == tokenizar("complejidad algoritmica datos")


def test_tokenizar_une_variantes_de_la_misma_palabra():
    assert tokenizar("validar") == tokenizar("validando") or tokenizar("validacion")[0] == tokenizar("validar")[0]


def test_condensar_quita_invisibles_y_corta():
    assert condensar("ig​nora\n\n  esto", 50) == "ig nora esto"
    assert len(condensar("a" * 100, 10)) == 10


def test_bm25_prefiere_el_documento_que_repite_el_termino_raro():
    docs = [tokenizar(t) for t in ["casos borde lista vacia", "nombres de variables claros", "complejidad temporal"]]
    assert BM25(docs).buscar(tokenizar("lista vacia"), 3)[0][0] == 0


def test_bm25_sin_coincidencias_no_devuelve_nada():
    assert BM25([tokenizar("hola mundo")]).buscar(tokenizar("zzz"), 3) == []


def test_rrf_premia_lo_que_ambos_recuperadores_traen():
    f = fusionar_rrf([1, 2, 3], [3, 4, 1])
    assert [x.indice for x in f][:2] == [1, 3]  # los dos estan en ambas listas
    assert f[0].rango_lexico == 1 and f[0].rango_semantico == 3


def test_rrf_un_item_solo_en_una_lista_conserva_none_en_la_otra():
    f = {x.indice: x for x in fusionar_rrf([7], [8])}
    assert f[7].rango_semantico is None and f[8].rango_lexico is None


def test_rrf_es_determinista_en_empates():
    assert fusionar_rrf([1], [2]) == fusionar_rrf([1], [2])


def test_trocear_parte_por_secciones_con_titulo_del_documento():
    fr = trocear("x.md", "# Doc\n\n## A\ntexto a\n\n## B\ntexto b\n")
    assert [f.titulo for f in fr] == ["Doc > A", "Doc > B"]
    assert fr[0].id == "x.md#1"


def test_trocear_parte_secciones_largas():
    cuerpo = "\n\n".join("palabra " * 60 for _ in range(6))
    assert len(trocear("x.md", f"# D\n\n## S\n{cuerpo}")) > 1


@pytest.fixture(scope="module")
def indice(tmp_path_factory) -> IndiceHibrido:
    return IndiceHibrido(cargar_corpus(RAIZ / "conocimiento"), VectorizadorHash(),
                         dir_cache=tmp_path_factory.mktemp("cache"))


@pytest.mark.parametrize(
    "consulta, archivo",
    [
        ("mi funcion falla con una lista vacia", "correccion-y-casos-borde.md"),
        ("mi codigo es dificil de leer, nombres de variables", "claridad-y-legibilidad.md"),
        ("dos bucles anidados O(n^2) como lo mejoro", "eficiencia-y-complejidad.md"),
        ("como escribo pruebas unitarias", "pruebas-y-validacion.md"),
        ("la camara y la pantalla se graban, puedo usar un asistente de IA", "integridad-y-uso-de-ia.md"),
    ],
)
def test_el_indice_hibrido_encuentra_el_documento_correcto(indice, consulta, archivo):
    assert archivo in [r.fragmento.fuente for r in indice.buscar(consulta, 3)]


def test_la_cache_de_vectores_se_reutiliza(tmp_path: Path):
    class Contador(VectorizadorHash):
        llamadas = 0

        def vectorizar(self, textos, tipo):
            if tipo == "documento":
                Contador.llamadas += 1
            return super().vectorizar(textos, tipo)

    fr = cargar_corpus(RAIZ / "conocimiento")
    IndiceHibrido(fr, Contador(), dir_cache=tmp_path)
    IndiceHibrido(fr, Contador(), dir_cache=tmp_path)
    assert Contador.llamadas == 1
