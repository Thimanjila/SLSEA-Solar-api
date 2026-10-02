# SLSEA Real-Time Solar Generation Data API

NB6007CEM Web API Development coursework implementation.

## Stack
- FastAPI
- SQLAlchemy
- PostgreSQL in deployment / SQLite for quick local development
- JWT bearer authentication with scopes
- OpenAPI / Swagger
- ETag + Last-Modified conditional GET
- Pagination, filtering and sorting
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

## Demo accounts after seeding

The seed script prints generated credentials. Do not use these credentials in the final public deployment documentation.

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

## Important coursework evidence

The final repository should contain incremental commits showing:
1. project bootstrap
2. data model
3. hierarchy read path
4. installation/composite/last-known resources
5. ingestion
6. pagination/filtering/sorting
7. conditional GET
8. error contract
9. JWT/scopes/jurisdiction enforcement
10. district summary
11. seed data and tests
12. deployment/documentation

AI-generated code must be disclosed in the report appendix according to the coursework brief.
