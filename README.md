# MeritIA · Mentor RAG híbrido

Servicio Python (FastAPI) que da retroalimentación al candidato combinando **sus resultados** con **material de estudio recuperado** de una base de conocimiento, y **muestra de dónde salió cada consejo**.

Mismo contrato que el mentor del `ai-service` (`POST /api/v1/mentor`) más el campo `fuentes`. Sin estado y sin acceso a la base del backend: todo llega en la petición.

## Contenido

1. [Cómo funciona](#cómo-funciona)
2. [Requisitos](#requisitos)
3. [Inicio rápido (sin API key)](#inicio-rápido-sin-api-key)
4. [Modo real con Gemini](#modo-real-con-gemini)
5. [Variables de entorno](#variables-de-entorno)
6. [Probar que funciona](#probar-que-funciona)
7. [Docker](#docker)
8. [Conectarlo al backend de MeritIA](#conectarlo-al-backend-de-meritia)
9. [API](#api)
10. [Ampliar la base de conocimiento](#ampliar-la-base-de-conocimiento)
11. [Problemas frecuentes](#problemas-frecuentes)
12. [Estructura del código](#estructura-del-código)
13. [Limitaciones conocidas](#limitaciones-conocidas)

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

- **Por qué híbrido:** BM25 acierta con términos exactos (`O(n²)`, `off-by-one`, `STAR`) y falla con sinónimos; los vectores entienden que "mi código es lento" ≈ "eficiencia" pero pueden dejar escapar un término raro. RRF fusiona **posiciones**, no puntajes, así que no hay pesos que calibrar entre escalas distintas.
- **La consulta no es solo la pregunta:** se le suman los criterios por debajo del 60 % y la evidencia del evaluador. Un "¿cómo mejoro?" recupera material sobre lo que de verdad le falla.
- **Transparencia:** cada fuente trae título, archivo, extracto y la posición que le dio cada recuperador. Si el modelo no cita nada, igual se devuelven los fragmentos que vio. Las citas a fragmentos inexistentes se descartan.
- **Defensas** (las mismas del ai-service): delimitador aleatorio alrededor de la pregunta, tratada como dato; historial acotado a 6 turnos de 400 caracteres; salida con tope y validada; errores sin detalle y con `reintentable`; el log nunca lleva la pregunta ni la respuesta.

## Requisitos

- **Python 3.11 o superior** (probado en 3.11; la imagen Docker usa 3.12). Comprueba con `python --version`.
- **Git** para clonar.
- Solo para el modo real: una **API key de Gemini** gratuita de <https://aistudio.google.com/apikey> (puede ser la misma que ya usa el `ai-service`).

No necesita base de datos, Redis ni otros servicios.

## Inicio rápido (sin API key)

Con esto corre completo en local, sin red: el "modelo" simulado responde con el mejor fragmento recuperado y los vectores son un hashing local. Sirve para ver la recuperación y para desarrollar.

**1. Clonar e instalar**

```bash
git clone https://github.com/MeritIA/rag-service.git
cd rag-service
python -m venv .venv
```

Activar el entorno virtual:

```bash
# Windows (PowerShell)
.venv\Scripts\Activate.ps1
# Windows (cmd)
.venv\Scripts\activate.bat
# macOS / Linux / Git Bash
source .venv/bin/activate        # en Git Bash de Windows: source .venv/Scripts/activate
```

```bash
pip install -r requirements-dev.txt
```

**2. Crear el `.env`**

```bash
# Windows (PowerShell / cmd)
copy .env.example .env
# macOS / Linux / Git Bash
cp .env.example .env
```

Genera una clave de acceso (mínimo 32 caracteres) y pégala en `CLAVE_DE_ACCESO=` dentro de `.env`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

El resto de valores del `.env.example` ya sirven para el modo sin API key (`PROVEEDOR_IA=simulado`, `EMBEDDINGS=hash`).

**3. Arrancar**

```bash
python -m uvicorn app.main:app_por_omision --factory --port 3200 --reload
```

Al arrancar indexa la base de conocimiento (tarda un segundo con vectores locales). Debes ver `Uvicorn running on http://127.0.0.1:3200`. Documentación interactiva en <http://127.0.0.1:3200/api/docs>.

**4. Verificar** → ver [Probar que funciona](#probar-que-funciona).

## Modo real con Gemini

Para respuestas redactadas por un modelo y recuperación semántica de verdad, cambia estas variables en `.env`:

```
PROVEEDOR_IA=gemini
EMBEDDINGS=gemini
GEMINI_API_KEY=<tu clave>
```

y reinicia. Notas:

- La **primera vez** que arranca vectoriza los 40 fragmentos con Gemini (una llamada por lotes de hasta 100) y guarda el resultado en `.cache/`. Los arranques siguientes no gastan embeddings, salvo que cambies un archivo de `conocimiento/` o `GEMINI_MODELO_EMBEDDINGS`/`EMBEDDINGS_DIMENSION` (la caché se invalida sola por huella del contenido y del modelo).
- Cada pregunta gasta **1 embedding** (la consulta) y **1 generación**.
- Si Gemini rechaza el modelo (`404`) o la cuota, el servicio responde `422` o `503` (ver [API](#api)); cambia `GEMINI_MODELO` por uno disponible para tu cuenta.
- **Producción:** `APP_ENV=production` rechaza arrancar con `PROVEEDOR_IA=simulado` o `EMBEDDINGS=hash`, y apaga `/api/docs`.

## Variables de entorno

| Variable | Por omisión | Qué hace |
|---|---|---|
| `APP_ENV` | `development` | `development`, `test` o `production`. En producción se prohíben los modos simulados y se apaga `/api/docs`. |
| `PORT` | `3200` | Solo documentación; el puerto real lo fija el comando `uvicorn --port`. |
| `CLAVE_DE_ACCESO` | — (**obligatoria**) | Secreto compartido; el backend lo envía como `Authorization: Bearer ...`. Mínimo 32 caracteres. |
| `PROVEEDOR_IA` | `gemini` | `gemini` o `simulado`. El `.env.example` trae `simulado`. |
| `EMBEDDINGS` | `gemini` | `gemini` o `hash` (local, no semántico). El `.env.example` trae `hash`. |
| `GEMINI_API_KEY` | vacía | Obligatoria si `PROVEEDOR_IA` o `EMBEDDINGS` es `gemini`. |
| `GEMINI_MODELO` | `gemini-3.5-flash` | Modelo que redacta la respuesta. |
| `GEMINI_MODELO_EMBEDDINGS` | `gemini-embedding-001` | Modelo de vectores. |
| `EMBEDDINGS_DIMENSION` | `768` | Dimensión de los vectores. |
| `TIEMPO_MAXIMO_MS` | `30000` | Tiempo máximo por llamada al proveedor. |
| `DIR_CONOCIMIENTO` | `./conocimiento` | Carpeta con los `.md` a indexar. |
| `DIR_CACHE` | `./.cache` | Dónde se guardan los vectores calculados. |
| `K_CANDIDATOS` | `20` | Cuántos trae cada recuperador antes de fusionar. |
| `K_FINAL` | `4` | Cuántos fragmentos llegan al modelo. |
| `PESO_LEXICO` / `PESO_SEMANTICO` | `1.0` / `1.0` | Peso de cada recuperador en la fusión. |
| `RRF_K` | `60` | Constante de RRF; subirla aplana la diferencia entre posiciones. |

Si falta algo obligatorio, el servicio **no arranca** y el error dice qué variable.

## Probar que funciona

**Pruebas automáticas** (no necesitan API key ni red):

```bash
python -m pytest -q
```

Deben pasar las 33.

**Con el servicio arrancado**, en otra terminal (reemplaza `TU_CLAVE` por tu `CLAVE_DE_ACCESO`):

```bash
# 1. Salud (pública): debe decir "estado":"ok" y "fragmentos":40
curl http://127.0.0.1:3200/api/v1/salud

# 2. Ver qué recupera el índice, sin llamar al modelo
curl -G "http://127.0.0.1:3200/api/v1/conocimiento/buscar" \
  --data-urlencode "q=mi solucion es lenta con muchos datos" \
  -H "Authorization: Bearer TU_CLAVE"

# 3. Una pregunta completa al mentor
curl -X POST http://127.0.0.1:3200/api/v1/mentor \
  -H "Authorization: Bearer TU_CLAVE" -H "Content-Type: application/json" \
  -d '{"contexto":{"totalEvaluaciones":1,"promedio":40,"perfil":[{"nombre":"Eficiencia","porcentaje":30,"veces":1}],"recientes":[]},"historial":[],"pregunta":"mi solucion es lenta, como la mejoro?"}'
```

En PowerShell, `curl` es un alias de otro comando: usa `curl.exe`, o prueba desde <http://127.0.0.1:3200/api/docs> con el botón *Authorize*.

Resultado esperado del paso 3: JSON con `respuesta`, `sugerencias`, `fuentes` (cada una con `titulo`, `archivo`, `extracto`, `rangoLexico`, `rangoSemantico`), `proveedor`, `modelo`. Sin la cabecera `Authorization` responde `401`.

## Docker

```bash
docker build -t meritia-rag .
docker run --rm -p 3200:3200 --env-file .env meritia-rag
```

- La imagen corre sin privilegios y escribe la caché de vectores en `/tmp/cache`.
- En `.env` pon `APP_ENV=production`, `PROVEEDOR_IA=gemini`, `EMBEDDINGS=gemini` y `GEMINI_API_KEY` para un despliegue real (en producción los modos simulados no arrancan).
- La caché se pierde al recrear el contenedor; el primer arranque vuelve a vectorizar (es una sola llamada por lotes).

## Conectarlo al backend de MeritIA

El backend ([`MeritIA/backend`](https://github.com/MeritIA/backend), PR #32) puede apuntar el mentor a este servicio. Las evaluaciones **no** pasan por aquí: siguen yendo al `ai-service`.

1. Arranca este servicio y anota su `CLAVE_DE_ACCESO`.
2. En el `.env` del **backend** añade:

   ```
   MENTOR_SERVICE_URL=http://127.0.0.1:3200
   MENTOR_SERVICE_API_KEY=<la misma CLAVE_DE_ACCESO de este servicio>
   ```

   Usa `127.0.0.1` y no `localhost` (en Windows `localhost` puede resolver a IPv6 y fallar). Si el backend corre **dentro de Docker** y este servicio en tu máquina, usa `http://host.docker.internal:3200`. Si ambos están en Docker, usa el nombre del servicio en la red compartida.
3. Reinicia el backend. Si dejas las dos variables vacías, el mentor vuelve a usar el `ai-service` y no devuelve `fuentes`.
4. El frontend ([`MeritIA/web`](https://github.com/MeritIA/web), PR #5) muestra las fuentes en un desplegable bajo cada respuesta del mentor.

Para comprobar la cadena completa: entra como candidato con al menos una evaluación, abre **Mentor IA**, haz una pregunta y revisa que la respuesta traiga el desplegable "De dónde sale esto". Si el backend responde "El mentor no está disponible", mira los logs de este servicio: si no hay ninguna petición, el problema es la URL/clave del backend; si hay `401`, la clave no coincide.

## API

Todas las rutas salvo `salud` exigen `Authorization: Bearer <CLAVE_DE_ACCESO>`.

| Ruta | Para qué |
|---|---|
| `POST /api/v1/mentor` | Pregunta del candidato → `respuesta`, `sugerencias`, `fuentes`, `proveedor`, `modelo`, `vectorizador` |
| `GET /api/v1/conocimiento/buscar?q=...` | Depurar: qué recupera el índice para una consulta, sin llamar al modelo |
| `GET /api/v1/salud` | Pública. Estado y número de fragmentos indexados |

**Cuerpo de `POST /api/v1/mentor`:** `contexto` (`totalEvaluaciones`, `promedio`, `perfil[]` ≤ 12, `recientes[]` ≤ 3), `historial[]` (`rol`: `candidato`|`mentor`, `texto`) y `pregunta` (1 a 500 caracteres). Es el mismo contrato del mentor del `ai-service`.

**Errores** (todos `{ codigo, mensaje, reintentable }`):

| HTTP | `codigo` | Reintentable | Cuándo |
|---|---|---|---|
| 400 | `VALIDACION` | no | La petición no cumple el contrato (lista los campos, nunca sus valores) |
| 401 | `NO_AUTENTICADO` | no | Falta la clave o no coincide |
| 422 | `SOLICITUD_RECHAZADA_POR_PROVEEDOR` | no | Clave de Gemini inválida, modelo inexistente, contenido bloqueado |
| 502 | `SALIDA_INVALIDA` | sí | El modelo respondió algo fuera del contrato |
| 503 | `PROVEEDOR_NO_DISPONIBLE` | sí | Caída, sobrecarga (429/5xx), red o tiempo agotado |
| 500 | `INTERNO` | no | Error no previsto; el detalle va al log con la `referencia` |

## Ampliar la base de conocimiento

Añade un `.md` en `conocimiento/` con un `# Título` y secciones `## ...`: cada sección es un fragmento (se parte por párrafos si pasa de 900 caracteres). Reinicia el servicio y se reindexa solo; con Gemini solo se pagan embeddings por lo que cambió el contenido. Comprueba el efecto con `GET /api/v1/conocimiento/buscar?q=...` antes de confiar en él.

## Problemas frecuentes

| Síntoma | Causa y arreglo |
|---|---|
| `ValidationError ... clave_de_acceso` al arrancar | Falta `CLAVE_DE_ACCESO` o tiene menos de 32 caracteres. |
| `Falta GEMINI_API_KEY` | `PROVEEDOR_IA` o `EMBEDDINGS` está en `gemini` sin clave. Ponla, o usa `simulado`/`hash`. |
| `...prohibidos en produccion` | Con `APP_ENV=production` no se admiten `simulado` ni `hash`. |
| `ModuleNotFoundError` | No activaste el entorno virtual o no corriste `pip install -r requirements-dev.txt`. |
| `No hay archivos .md con contenido` | `DIR_CONOCIMIENTO` apunta a una carpeta equivocada o vacía. |
| `422 SOLICITUD_RECHAZADA_POR_PROVEEDOR` | Modelo inexistente para tu cuenta (`GEMINI_MODELO`) o clave inválida. |
| `503 PROVEEDOR_NO_DISPONIBLE` | Gemini saturado o sin cuota; reintenta en unos segundos. |
| Las respuestas empiezan con `[simulado]` | Estás con `PROVEEDOR_IA=simulado`. Ver [Modo real con Gemini](#modo-real-con-gemini). |
| La recuperación no encuentra sinónimos | Con `EMBEDDINGS=hash` no hay semántica real; usa `gemini`. |
| Puerto 3200 ocupado | Cambia `--port` y la `MENTOR_SERVICE_URL` del backend. |

## Estructura del código

```
app/
  main.py        API, autenticación y manejo de errores
  mentor.py      Consulta, prompt, validación de salida y citas
  schemas.py     Contrato HTTP (camelCase, igual que el ai-service)
  config.py      Variables de entorno
  rag/           texto (tokenizador) · bm25 · embeddings · fusion (RRF) · indice (corpus + caché)
  llm/           base (interfaz y errores) · gemini · simulado
conocimiento/    Base de conocimiento en Markdown
tests/           33 pruebas (sin red ni API key)
```

Cambiar de proveedor de modelo es escribir otro archivo en `app/llm/` que cumpla `Generador` y elegirlo en `crear_generador` (`app/main.py`).

## Limitaciones conocidas

- **Calidad con Gemini sin medir.** Las pruebas cubren la mecánica con vectores locales; falta un conjunto de preguntas de referencia que mida la recuperación semántica real.
- **No usa las señales de la grabación** (cámara/pantalla). Hoy el mentor solo usa evaluaciones. Si se quieren consejos del tipo "cambiaste de ventana 12 veces", el backend tendría que enviar un resumen de la sesión y hay que decidir su base de consentimiento.
- **La base de conocimiento es un primer borrador** de 7 guías; conviene que el equipo la revise.
- **Sin límite de peticiones propio**: el control de admisión del mentor está en el backend (`MENTOR_MAXIMO_EN_VUELO`).
