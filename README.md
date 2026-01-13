# qCT Dashboard

Read-only dashboard for simulated qCT outputs.

## Descripcion general

La app es un dashboard web construido con FastAPI + Jinja2 que presenta resultados simulados de estudios de imagen. El flujo principal es:

- Overview: indicadores agregados, distribucion de riesgo y tendencia de volumen promedio.
- Studies: lista filtrable de estudios y acceso al detalle.
- Study Detail: preview de imagen, resumen qCT y tabla de nodulos detectados.
- Follow-ups: timeline de comparaciones longitudinales simuladas.
- Ingestion: log de eventos de ingesta y procesamiento simulados.

La app es de solo lectura. No hay operaciones de escritura en UI; los datos se generan con el script de seed.

## Modelo de datos (resumen)

Entidad y relacion principal:

- Client: cliente principal. Tiene muchos Site.
- Site: sitio/clinica. Tiene muchos Patient y Study.
- Patient: paciente anonimo. Tiene muchos Study.
- Study: estudio por paciente y sitio, con fecha, estado y riesgo. Tiene Series, QCTSummary, QCTNodule, Image y logs.
- Series: serie de imagenes asociada al estudio.
- Image: archivo de imagen (placeholder) asociado a una serie.
- QCTSummary: resumen agregado del estudio (volumen total, diametro medio, VDT, riesgo).
- QCTNodule: nodulos detectados para el estudio (volumen, diametro, VDT, riesgo).
- QCTFollowup: comparacion entre dos estudios del mismo paciente para un nodulo (crecimiento y estado).
- IngestionLog: eventos de ingesta por estudio (estado, mensaje, timestamps).
- AccessAudit: auditoria de acceso a estudios (usuario, IP, fecha).
- User: usuario simulador (viewer).

Relaciones clave:

- Site -> Patient (1:N)
- Patient -> Study (1:N)
- Study -> Series -> Image (1:N, 1:N)
- Study -> QCTSummary (1:1)
- Study -> QCTNodule (1:N)
- QCTNodule -> QCTFollowup (1:N)
- Study -> IngestionLog (1:N)
- Study -> AccessAudit (1:N)

## Fuentes de datos

Los datos se generan en `scripts/seed_fake_data.py`. El script:

- Crea placeholders de imagen en `images/mock_ct`.
- Inserta pacientes, estudios, series, imagenes y nodulos.
- Calcula el resumen qCT por estudio.
- Genera followups entre estudios consecutivos de un paciente.
- Inserta ingestion logs y accesos simulados.

Esto permite tener un dashboard completo sin dependencia de datos reales.

## Despliegue en produccion (sugerido)

### Arquitectura recomendada

- App FastAPI con Uvicorn/Gunicorn en contenedor.
- Base de datos PostgreSQL.
- Almacenamiento de imagenes en volumen o bucket (S3 compatible).
- Reverse proxy (Nginx/Traefik) con TLS.

### Variables de entorno

Config base en `app/core/config.py`:

- `DATABASE_URL`: URL de PostgreSQL.
- `ENVIRONMENT`: entorno (dev/demo/prod).
- `AUTH_FAKE_USER`: usuario demo para auditoria.
- `DATA_SOURCE`: origen de datos (`mock` u `orthanc`).
- `ALLOW_PHI`: permitir datos de paciente reales (default `false`).
- `ORTHANC_URL`: base URL de Orthanc (default `http://localhost:8042`).
- `ORTHANC_USERNAME`: usuario de Orthanc (opcional).
- `ORTHANC_PASSWORD`: password de Orthanc (opcional).
- `LOG_LEVEL`: nivel de log (`INFO`, `DEBUG`, etc).
- `REQUEST_ID_HEADER`: header de correlacion (`X-Request-ID`).
- `CORS_ALLOW_ORIGINS`: lista CSV de origins permitidos.
- `CORS_ALLOW_METHODS`: lista CSV de metodos permitidos.
- `CORS_ALLOW_HEADERS`: lista CSV de headers permitidos.
- `CORS_ALLOW_CREDENTIALS`: permitir credenciales en CORS.
- `READY_CHECK_DB`: habilitar check de DB en readiness.
- `DB_POOL_SIZE`: pool size de SQLAlchemy.
- `DB_MAX_OVERFLOW`: max overflow del pool.
- `DB_POOL_TIMEOUT`: timeout del pool (segundos).
- `DB_POOL_RECYCLE`: recycle del pool (segundos).
- `DB_CONNECT_TIMEOUT`: timeout de conexion (segundos).
- `DB_STATEMENT_TIMEOUT_MS`: timeout de statement (ms, 0 desactiva).

### Build y runtime

1. Construir imagen:
   ```bash
   docker build -t qct-dashboard:latest .
   ```
2. Correr en produccion (ejemplo con Docker/Gunicorn):
   ```bash
   docker run -d \
     -p 8000:8000 \
     -e DATABASE_URL=postgresql+psycopg2://user:pass@db:5432/qct \
     -e ENVIRONMENT=prod \
     -e AUTH_FAKE_USER=demo_user \
     -e LOG_LEVEL=INFO \
     -e READY_CHECK_DB=true \
     -e WEB_CONCURRENCY=2 \
     -e GUNICORN_TIMEOUT=60 \
     -v /data/qct/images:/app/images \
     qct-dashboard:latest
   ```
3. Migraciones:
   ```bash
   alembic upgrade head
   ```

### Notas de produccion

- El seed debe ejecutarse solo en entornos de demo.
- Para datos reales, reemplazar el pipeline de ingesta y desactivar placeholders.
- Configurar CORS y autenticacion real si se expone publicamente.
- Escalar Uvicorn/Gunicorn con multiples workers en host con CPU suficiente.

### Healthchecks

- `/_healthz`: responde `{"status":"ok"}` si la app esta viva.
- `/_readyz`: responde `{"status":"ok"}` si la app esta lista (opcionalmente valida DB).

## Quickstart

1. Start PostgreSQL:
   ```bash
   docker-compose up -d
   ```
2. Create schema:
   ```bash
   alembic upgrade head
   ```
3. Seed demo data:
   ```bash
   python scripts/seed_fake_data.py
   ```
4. Run the app:
   ```bash
   uvicorn app.main:app --reload
   ```

Visit http://localhost:8000
