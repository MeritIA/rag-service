# MeritIA · Mentor RAG híbrido

Servicio Python (FastAPI) que da retroalimentación al candidato combinando **sus resultados** con **material de estudio recuperado** de una base de conocimiento, y **muestra de dónde salió cada consejo**.

Mismo contrato que el mentor del `ai-service` (`POST /api/v1/mentor`), más el campo `fuentes`. Sin estado y sin acceso a la base del backend: todo llega en la petición.

## Cómo funciona

```
pregunta + criterios flojos + evidencia ──► consulta
                                              │
                    ┌─────────────────────────┴───────────────────────┐
                    ▼                                                 ▼
             BM25 (léxico)                              Vectores (semántico, Gemini)
             top 20 por palabras                        top 20 por significado
                    └──────────────► Fusión RRF ◄─────────────────────┘
                                          │  top 4 fragmentos
                                          ▼
          RESUMEN del candidato + FRAGMENTOS [1..4] + PREGUNTA ──► LLM
                                          ▼
                respuesta citando [n]  +  fuentes (con rango léxico/semántico)
```

- **Por qué híbrido:** BM25 acierta con términos exactos (`O(n²)`, `off-by-one`, `STAR`) y falla con sinónimos; los vectores entienden "mi código es lento" ≈ "eficiencia" pero pueden dejar escapar un término raro. RRF fusiona **posiciones**, no puntajes, así que no hay pesos que calibrar entre escalas distintas.
- **La consulta no es solo la pregunta:** se le suman los criterios por debajo del 60 % y la evidencia del evaluador. Un "¿cómo mejoro?" recupera material sobre lo que de verdad le falla.
- **Transparencia ("ver las respuestas"):** cada fuente trae título, archivo, extracto y en qué posición la puso cada recuperador. Si el modelo no cita nada, igual se devuelven los fragmentos que vio. Las citas a fragmentos inexistentes se descartan.
- **Defensas** (las mismas del ai-service): delimitador aleatorio alrededor de la pregunta, tratada como dato; historial acotado a 6 turnos de 400 caracteres; salida con tope y validada; errores sin detalle y con `reintentable`; el log nunca lleva la pregunta ni la respuesta.

## Arrancar

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env   # pon CLAVE_DE_ACCESO (>= 32 caracteres)
python -m uvicorn app.main:app_por_omision --factory --port 3200 --reload
```

Con `PROVEEDOR_IA=simulado` y `EMBEDDINGS=hash` (valores por omisión del `.env.example`) corre **sin API key ni red**; el simulado responde con el mejor fragmento. Para la versión real: `PROVEEDOR_IA=gemini`, `EMBEDDINGS=gemini` y `GEMINI_API_KEY`. Ambos modos simulados están prohibidos con `APP_ENV=production`.

Docs interactivas en `/api/docs` (apagadas en producción).

```bash
python -m pytest -q
```

## Endpoints (Bearer `CLAVE_DE_ACCESO`)

| Ruta | Para qué |
|---|---|
| `POST /api/v1/mentor` | Pregunta del candidato → `respuesta`, `sugerencias`, `fuentes`, `proveedor`, `modelo`, `vectorizador` |
| `GET /api/v1/conocimiento/buscar?q=...` | Depurar: qué recupera el índice para una consulta, sin llamar al modelo |
| `GET /api/v1/salud` | Pública. Estado y número de fragmentos indexados |

## Ampliar la base de conocimiento

Añade un `.md` en `conocimiento/` con un `# Título` y secciones `## ...`: cada sección es un fragmento (se parte por párrafos si pasa de 900 caracteres). Al reiniciar se reindexa solo; los vectores se cachean en `.cache/` por huella del contenido y del modelo, así que solo se pagan embeddings por lo que cambió.

## Conectarlo al backend

Ya está cableado. En el `.env` del backend:

```
MENTOR_SERVICE_URL=http://127.0.0.1:3200
MENTOR_SERVICE_API_KEY=<la misma CLAVE_DE_ACCESO de este servicio>
```

Si quedan vacías, el mentor sigue usando el `ai-service` como antes (sin `fuentes`). Las evaluaciones no cambian: siguen yendo a `AI_SERVICE_URL`. `GET /api/v1/mentor` del backend ahora devuelve `fuentes` (`n`, `titulo`, `archivo`, `extracto`), acotadas en tamaño y número; el frontend aún no las muestra.

## Lo que falta

- **Calidad con Gemini sin medir.** Las pruebas cubren la mecánica con vectores locales; no hay todavía un conjunto de preguntas de referencia que compare la recuperación semántica real (análogo a `test/calibracion` del ai-service).
- **Señales de la grabación** (cámara/pantalla). Hoy el mentor solo usa evaluaciones. Si se quieren consejos del tipo "cambiaste de ventana 12 veces", el backend tendría que enviar un resumen de la sesión y hay que decidir su base de consentimiento.
- La base de conocimiento es un primer borrador de 7 guías; conviene que el equipo la revise.
