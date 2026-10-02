# Manual Smoke Test Checklist

Use Swagger at `/docs`.

## 1. Health
GET /health -> 200

## 2. Authentication
POST /api/v1/auth/token
- national_analyst
- district_analyst
- device_001

## 3. Read path
- GET /api/v1/provinces
- GET /api/v1/provinces/1/districts
- GET /api/v1/districts
- GET /api/v1/districts/1/grid-substations
- GET /api/v1/grid-substations/1/installations
- GET /api/v1/installations/1
- GET /api/v1/installations/1/composite
- GET /api/v1/installations/1/last-known-reading

## 4. Analytical history
GET /api/v1/installations/1/readings?limit=10&offset=0&sort=desc
GET /api/v1/installations/1/readings?limit=10&offset=10&sort=asc
Add from_time/to_time and jurisdiction filters.

## 5. Device write
Use device_001 token:
POST /api/v1/installations/1/readings
Confirm 201 and Location header.

Try posting to installation 2 and confirm 403.

## 6. Security
Use district_analyst token and request a resource belonging to another district.
Expected: 403.

## 7. Conditional GET
GET a resource, copy ETag, then send:
If-None-Match: <etag>
Expected target: 304 with empty body.

Implementation note:
The starter includes ETag/Last-Modified headers. Add explicit If-None-Match / If-Modified-Since handling as the next development increment before final submission.
