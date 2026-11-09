# Eficiencia y complejidad algorítmica

## Qué mide el criterio de eficiencia
La eficiencia mide cómo crecen el tiempo y la memoria de tu solución cuando crece la entrada. No se trata de micro-optimizar, sino de elegir un enfoque que no se vuelva inviable con datos grandes.

## Notación Big-O en la práctica
O(1) es constante, O(log n) crece muy despacio (búsqueda binaria), O(n) recorre una vez, O(n log n) es el costo típico de ordenar y O(n²) aparece con dos bucles anidados sobre la misma colección. Indica siempre la complejidad de tiempo y de espacio de tu solución, aunque el enunciado no la pida.

## Señales de que puedes mejorar
Dos bucles anidados que buscan un elemento suelen poder reemplazarse por un diccionario o conjunto (hash), que busca en O(1) promedio. Ordenar primero y luego usar dos punteros suele bajar de O(n²) a O(n log n). Recalcular lo mismo varias veces se arregla guardando el resultado (memoización) o precalculando.

## Estructura de datos adecuada
Elige la estructura por la operación que más usas: lista para acceso por posición, conjunto para pertenencia, diccionario para asociar clave y valor, cola para orden de llegada, pila para deshacer o recorrer en profundidad, montículo para sacar siempre el mínimo o máximo. Buscar un elemento en una lista es O(n); en un conjunto es O(1).

## Cómo comunicar el compromiso
Si eliges una solución más lenta pero más simple, dilo: "Es O(n²) pero con n ≤ 100 es suficiente y más fácil de verificar". Explicar el compromiso demuestra criterio. Empieza por una solución correcta, mide, y solo entonces optimiza.

## Errores comunes
Concatenar cadenas dentro de un bucle crea copias en cada vuelta (usa una lista y `join`). Copiar una lista completa dentro de un bucle convierte un O(n) en O(n²). Usar recursión sin caso base o sin memoización puede dar tiempo exponencial.
