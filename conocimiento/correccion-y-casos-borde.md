# Corrección y casos borde

## Qué mide el criterio de corrección
La corrección responde a una sola pregunta: ¿el programa hace lo que pide el enunciado en todas las entradas válidas? Una solución que funciona con el ejemplo del enunciado pero falla con una lista vacía no es correcta, es una solución que no se probó.

## Casos borde que casi siempre se evalúan
Antes de escribir código, enumera las entradas límite: colección vacía, un solo elemento, elementos repetidos, valores negativos o cero, cadenas vacías, números muy grandes, valores nulos y entradas ya ordenadas o en orden inverso. Escribirlos en un comentario al inicio te obliga a decidir qué debe pasar en cada uno.

## Errores comunes de corrección
El error más frecuente es el desfase de uno (off-by-one) en índices y rangos: revisa si el límite es inclusivo o exclusivo. Otro es modificar la entrada cuando el enunciado dice que no se debe: una función que invierte una lista pero altera la original incumple el contrato aunque el resultado se vea bien. También es común no manejar el caso vacío y fallar con un error de índice.

## Cómo verificar antes de entregar
Haz una prueba de escritorio con una entrada pequeña, paso a paso, anotando el valor de cada variable. Después ejecuta tus propios casos borde, no solo el ejemplo del enunciado. Si dudas entre dos interpretaciones del enunciado, escribe la suposición que tomaste en un comentario: un evaluador valora una suposición explícita más que una silenciosa.

## Mutación de datos y efectos secundarios
Si el enunciado pide devolver un resultado nuevo, trabaja sobre una copia. Evita variables globales y estado compartido entre llamadas: hacen que la misma entrada dé resultados distintos y son una causa típica de fallos intermitentes.
