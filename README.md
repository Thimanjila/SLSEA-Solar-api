# SLSEA Real-Time Solar Generation Data API

NB6007CEM Web API Development coursework implementation.

## Stack

- SQLAlchemy
- PostgreSQL in deployment / SQLite for quick local development
- JWT bearer authentication with scopes
- OpenAPI / Swagger
- ETag + Last-Modified conditional GET
- Pagination, filtering and sorting
- Added pagination with limit and offset
- Added ascending and descending sorting
- Added time-range filtering
- Added province, district, and substation filtering
- Added pagination next/previous links
- Added ETag conditional GET support
- Tested HTTP 304 Not Modified responses
- Seed data generator

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python seed.py
uvicorn app.main:app --reload
```

Open:
- http://127.0.0.1:8000/docs
- http://127.0.0.1:8000/openapi.json
- http://127.0.0.1:8000/health


## Main resources

- /api/v1/provinces
- /api/v1/districts
- /api/v1/grid-substations
- /api/v1/installations
- /api/v1/installations/{installation_id}
- /api/v1/installations/{installation_id}/composite
- /api/v1/installations/{installation_id}/last-known-reading
- /api/v1/installations/{installation_id}/readings
- /api/v1/districts/{district_id}/generation-summary
- /api/v1/auth/token

