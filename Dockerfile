FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app ./app
COPY conocimiento ./conocimiento
# Sin privilegios; la cache de vectores va a /tmp para poder correr con el FS de solo lectura.
RUN useradd -r -u 10001 mentor
USER mentor
ENV DIR_CACHE=/tmp/cache
EXPOSE 3200
CMD ["uvicorn", "app.main:app_por_omision", "--factory", "--host", "0.0.0.0", "--port", "3200"]
