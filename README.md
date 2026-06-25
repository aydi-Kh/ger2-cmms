# GER2 Medical Centers — Advanced CMMS

Computerized Maintenance Management System for GER2 Medical Centers.

## Architecture

```
ger2_cmms/
├── backend/          FastAPI 0.111 · Python 3.12 · PostgreSQL 16 + TimescaleDB
│   ├── app/
│   │   ├── api/v1/routers/    assets · workorders · ai_agents · compliance · costs · auth
│   │   ├── models/            SQLAlchemy 2.0 async ORM models
│   │   ├── schemas/           Pydantic v2 request/response schemas
│   │   ├── core/              config · database · security · cache · logging
│   │   └── integrations/      DICOM · OPC-UA · HL7 FHIR · Kafka
│   └── alembic/              Database migrations
├── agents/
│   ├── predictor/    LSTM + Kaplan-Meier RUL ensemble (ONNX)
│   ├── scheduler/    Constraint satisfaction + FHIR R4 slot management
│   ├── cost/         Cost accumulation + budget variance
│   ├── compliance/   Cert expiry monitoring + DICOM SR write-back
│   └── diagnostics/  Isolation Forest + CNN anomaly detection
├── frontend/         React 18 · TypeScript · Vite · Zustand · React Query
├── infra/
│   ├── docker/       Dockerfiles
│   ├── k8s/          Kubernetes manifests (base + staging + production overlays)
│   ├── prometheus/   Metrics scrape config
│   └── grafana/      Dashboard definitions
└── tests/
    ├── unit/         pytest — 70% coverage target
    ├── integration/  API contract tests
    ├── e2e/          Playwright browser automation
    └── load/         k6 performance tests (p95 < 200ms / 200 VUs)

## Quick Start

```bash
cp .env.example backend/.env
docker-compose up -d
# API: http://localhost:8000/api/v1/docs
# Frontend: http://localhost:3000
# Grafana: http://localhost:3001 (admin / ger2admin)
```

## Running Tests

```bash
# Unit tests
cd backend && pytest tests/unit -v --cov=app

# Integration tests (requires running stack)
API_BASE_URL=http://localhost:8000 pytest tests/integration -m integration

# Load test (requires k6)
k6 run tests/load/k6_api_load_test.js -e API_BASE_URL=http://localhost:8000
```
