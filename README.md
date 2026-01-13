# qCT Dashboard

Read-only dashboard for simulated qCT outputs.

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
