# Pruebas y validación de entradas

## Por qué probar forma parte de la nota
Entregar pruebas demuestra que verificaste tu propio trabajo. Los reclutadores leen las pruebas como evidencia de disciplina: quien prueba encuentra sus propios errores antes que el evaluador.

## Qué probar
Cubre el caso típico, los casos borde (vacío, un elemento, repetidos, negativos), los casos de error (entrada inválida) y al menos un caso grande. Un buen conjunto de pruebas es pequeño pero cada prueba existe por una razón distinta.

## Estructura de una prueba
Sigue el patrón organizar, actuar, afirmar (arrange, act, assert): prepara los datos, llama a la función, compara con el resultado esperado. Una prueba debe fallar por un único motivo y tener un nombre que describa el comportamiento: `test_invertir_lista_vacia_devuelve_lista_vacia`.

## Validación de entradas
Valida en los límites del sistema: lo que llega del usuario, de un archivo o de la red. Decide qué hacer ante lo inválido: lanzar una excepción clara con un mensaje útil suele ser mejor que devolver `None` en silencio. No uses `assert` para validar datos del usuario, porque puede desactivarse.

## Manejo de errores
Captura la excepción más específica posible, no un `except:` genérico que oculte fallos. No tragues errores sin registrarlos. Si capturas una excepción, decide si puedes recuperarte; si no, vuelve a lanzarla con contexto.

## Probar antes de optimizar
Las pruebas te dejan refactorizar y optimizar sin miedo a romper el comportamiento. Escribe primero la prueba del caso que te preocupa y luego haz que pase.
