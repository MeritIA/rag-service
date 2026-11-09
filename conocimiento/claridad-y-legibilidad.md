# Claridad y legibilidad del código

## Qué mide el criterio de claridad
La claridad mide si otra persona puede leer tu solución y entenderla sin que se la expliques. El código se lee muchas más veces de las que se escribe; en una prueba técnica, el evaluador es ese lector y tiene pocos minutos.

## Nombres que comunican
Usa nombres que digan qué es la cosa, no cómo se calculó: `precio_con_descuento` en lugar de `x2` o `tmp`. Las funciones se nombran con un verbo (`calcular_total`, `validar_correo`) y los booleanos como pregunta (`es_valido`, `tiene_permiso`). Una sola letra solo es aceptable en índices de un bucle corto.

## Funciones pequeñas con una responsabilidad
Si una función hace tres cosas, sepárala en tres. Una función que se puede resumir sin usar la palabra "y" suele estar bien dividida. Evita el anidamiento profundo: usa retornos tempranos (guard clauses) para tratar primero los casos inválidos y dejar el camino principal sin sangrías extra.

## Comentarios útiles
Comenta el porqué, no el qué. `i += 1  # suma uno a i` no aporta nada; `# se salta la cabecera del CSV` sí. Si necesitas un comentario largo para explicar un bloque, probablemente ese bloque merece ser una función con buen nombre.

## Estructura y consistencia
Mantén un formato consistente (sangría, comillas, orden de importaciones). Elimina código muerto, variables sin usar y `print` de depuración antes de entregar. Evita números mágicos: `if edad >= 18` se entiende mejor como `EDAD_MINIMA = 18`.

## Código ilegible que funciona
Una solución puede ser correcta y aun así sacar poca nota en claridad: si un evaluador no puede seguirla, no puede confiar en ella. Prefiere la versión simple y explícita a la ingeniosa y comprimida.
