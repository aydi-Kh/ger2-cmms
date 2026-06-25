# GER2 CMMS — Step-by-Step Installation Manual

This manual explains how to install, configure, run, test, and deploy the GER2 Medical Centers CMMS solution.

## 1. Solution Overview

The GER2 CMMS codebase is structured as a production-oriented monorepo:

```text
ger2_cmms/
├── backend/          FastAPI API, SQLAlchemy models, Alembic migrations
├── agents/           Predictor, Scheduler, Cost, Compliance AI agents
├── frontend/         React 18 + TypeScript + Vite application
├── infra/            Docker, Kubernetes, Prometheus/Grafana configuration
├── tests/            Unit, integration and k6 load tests
├── docker-compose.yml
├── .env.example
└── README.md
```

Core services:

| Service | Purpose | Default URL |
|---|---|---|
| Backend API | FastAPI REST API | http://localhost:8000 |
| API Documentation | Swagger / OpenAPI | http://localhost:8000/api/v1/docs |
| Frontend | React CMMS UI | http://localhost:3000 |
| PostgreSQL + TimescaleDB | Main database + time-series sensor data | localhost:5432 |
| Redis | Cache layer | localhost:6379 |
| Kafka | Event bus for agents and integrations | localhost:9092 |
| MLflow | AI model registry | http://localhost:5000 |
| Prometheus | Metrics collection | http://localhost:9090 |
| Grafana | Monitoring dashboards | http://localhost:3001 |

---

## 2. Prerequisites

Install the following tools before starting:

| Tool | Recommended Version | Purpose |
|---|---:|---|
| Git | 2.40+ | Clone and manage source code |
| Docker | 24+ | Run containers |
| Docker Compose | v2+ | Run the full local stack |
| Python | 3.12 | Backend development and tests |
| Node.js | 20 LTS | Frontend development |
| npm | 10+ | Frontend package manager |
| kubectl | 1.30+ | Kubernetes deployment |
| k6 | Latest | Load testing |

Check versions:

```bash
git --version
docker --version
docker compose version
python3 --version
node --version
npm --version
```

---

## 3. Clone the Repository

```bash
git clone https://github.com/aydi-Kh/ger2-cmms.git
cd ger2-cmms
```

If the repository contains the code inside a `ger2_cmms/` subfolder, enter it:

```bash
cd ger2_cmms
```

---

## 4. Environment Configuration

Copy the environment template:

```bash
cp .env.example backend/.env
```

Open `backend/.env` and update at least the following variables:

```env
DATABASE_URL=postgresql+asyncpg://ger2:CHANGE_ME@postgres:5432/ger2_cmms
REDIS_URL=redis://redis:6379/0
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
SECRET_KEY=GENERATE_A_SECURE_32_BYTE_RANDOM_SECRET
DICOM_AE_TITLE=GER2_CMMS
DICOM_WADO_RS_URL=http://orthanc:8042/wado
DICOM_STOW_RS_URL=http://orthanc:8042/instances
OPCUA_SERVER_URL=opc.tcp://opcua-server:4840
FHIR_SERVER_URL=http://fhir:8080/fhir
MLFLOW_TRACKING_URI=http://mlflow:5000
```

Generate a secure secret key:

```bash
python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
```

Important security note: never commit real passwords, tokens, API keys, private keys, DICOM credentials, or production secrets to GitHub.

---

## 5. Local Installation with Docker Compose

Start the full stack:

```bash
docker compose up -d --build
```

Check running containers:

```bash
docker compose ps
```

Follow logs:

```bash
docker compose logs -f backend
docker compose logs -f agent-predictor
docker compose logs -f frontend
```

Run database migrations manually if needed:

```bash
docker compose exec backend alembic upgrade head
```

---

## 6. Access the Application

After startup, open:

| Component | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend health | http://localhost:8000/health |
| API docs | http://localhost:8000/api/v1/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |
| MLflow | http://localhost:5000 |

Grafana default local credentials:

```text
Username: admin
Password: ger2admin
```

Change the Grafana password before any production usage.

---

## 7. Backend Development Setup

For local backend development outside Docker:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Run migrations:

```bash
alembic upgrade head
```

Create a new migration:

```bash
alembic revision --autogenerate -m "describe_change"
```

---

## 8. Frontend Development Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend development server:

```text
http://localhost:3000
```

Build production frontend:

```bash
npm run build
npm run preview
```

---

## 9. AI Agents

The AI agents communicate through Kafka topics.

| Agent | Path | Main Role |
|---|---|---|
| Predictor Agent | `agents/predictor/predictor_agent.py` | RUL inference, anomaly scoring, auto-WO trigger |
| Scheduler Agent | `agents/scheduler/scheduler_agent.py` | Technician assignment, FHIR Slot creation |
| Cost Agent | `agents/cost/cost_agent.py` | Labor/parts cost accumulation, budget events |
| Compliance Agent | `agents/compliance/compliance_agent.py` | Calibration expiry, DICOM SR write-back, evidence-pack queue |

Run agents with Docker Compose:

```bash
docker compose up -d agent-predictor agent-scheduler agent-cost agent-compliance
```

Run one agent manually for development:

```bash
cd agents/predictor
python3 predictor_agent.py
```

Kafka topics used by the solution:

```text
ger2.sensor.raw
ger2.agent.events
ger2.wo.commands
ger2.compliance.events
ger2.cost.events
ger2.dicom.events
ger2.audit.log
```

---

## 10. DICOM, OPC-UA and FHIR Configuration

### DICOM

Configure DICOM endpoints in `backend/.env`:

```env
DICOM_AE_TITLE=GER2_CMMS
DICOM_WADO_RS_URL=http://orthanc:8042/wado
DICOM_STOW_RS_URL=http://orthanc:8042/instances
```

DICOM functions are implemented in:

```text
backend/app/integrations/dicom/client.py
```

Supported operations:

- DICOMweb WADO-RS metadata retrieval
- DICOMweb STOW-RS Structured Report storage
- DICOM PS3.15 Profile E de-identification

### OPC-UA

Configure OPC-UA endpoint:

```env
OPCUA_SERVER_URL=opc.tcp://opcua-server:4840
OPCUA_SECURITY_POLICY=Basic256Sha256
OPCUA_SECURITY_MODE=SignAndEncrypt
```

OPC-UA polling client:

```text
backend/app/integrations/opcua/client.py
```

### HL7 FHIR R4

Configure FHIR endpoint:

```env
FHIR_SERVER_URL=http://fhir:8080/fhir
FHIR_VERSION=R4
```

The Scheduler Agent creates FHIR Slot resources for maintenance windows.

---

## 11. Running Tests

### Backend unit tests

```bash
pytest tests/unit/backend -v
```

With coverage:

```bash
pytest tests/unit/backend -v --cov=backend/app --cov-report=term-missing
```

### Integration tests

Start the stack first:

```bash
docker compose up -d
```

Then run:

```bash
API_BASE_URL=http://localhost:8000 pytest tests/integration -v
```

### Load tests with k6

```bash
k6 run tests/load/k6_api_load_test.js -e API_BASE_URL=http://localhost:8000/api/v1
```

Performance targets:

| Metric | Target |
|---|---:|
| API p95 latency | < 200 ms |
| Dashboard load | < 1 s |
| Work order creation | < 500 ms |
| AI inference event processing | < 2 s |
| Concurrent users | 200 |
| Kafka throughput | 10,000 events/min |

---

## 12. Production Deployment on Kubernetes

### 12.1 Build and push container images

```bash
docker build -t ghcr.io/aydi-kh/ger2-backend:latest backend
docker build -t ghcr.io/aydi-kh/ger2-frontend:latest frontend
```

Push images:

```bash
docker push ghcr.io/aydi-kh/ger2-backend:latest
docker push ghcr.io/aydi-kh/ger2-frontend:latest
```

### 12.2 Create namespace

```bash
kubectl create namespace ger2-prod
```

### 12.3 Create secrets

Use your real production values:

```bash
kubectl -n ger2-prod create secret generic ger2-backend-secrets \
  --from-literal=DATABASE_URL='postgresql+asyncpg://USER:PASSWORD@HOST:5432/ger2_cmms' \
  --from-literal=REDIS_URL='redis://redis:6379/0' \
  --from-literal=KAFKA_BOOTSTRAP_SERVERS='kafka:9092' \
  --from-literal=SECRET_KEY='REPLACE_WITH_SECURE_SECRET'
```

### 12.4 Apply manifests

```bash
kubectl apply -k infra/k8s/overlays/production
```

Check rollout:

```bash
kubectl -n ger2-prod rollout status deployment/ger2-backend
kubectl -n ger2-prod get pods
kubectl -n ger2-prod get svc
```

---

## 13. CI/CD Pipeline

GitHub Actions pipeline:

```text
.github/workflows/ci-cd.yml
```

Pipeline stages:

1. Unit tests
2. Trivy security scan
3. Build and push Docker images
4. Deploy to staging
5. Integration tests
6. Deploy to production

Required GitHub secrets:

| Secret | Purpose |
|---|---|
| `GITHUB_TOKEN` | Container registry push |
| `STAGING_KUBECONFIG` | Staging Kubernetes access |
| `PROD_KUBECONFIG` | Production Kubernetes access |
| `STAGING_API_URL` | Integration test target |

---

## 14. Backup and Disaster Recovery

Recommended minimum backup schedule:

| Component | Frequency | Retention |
|---|---:|---:|
| PostgreSQL database | Every 6 hours | 30 days |
| TimescaleDB sensor data | Daily | 90 days |
| Calibration certificates | Daily | 7 years |
| Audit logs | Continuous export | 7 years |
| MLflow model registry | Daily | 1 year |

Target recovery objectives:

| Metric | Target |
|---|---:|
| RPO | 15 minutes for critical data |
| RTO | 2 hours for full platform restore |

---

## 15. Operational Checklist

Before production go-live:

- [ ] All environment variables configured with production values
- [ ] No hardcoded secrets in source code
- [ ] PostgreSQL backup job tested
- [ ] Redis memory limit configured
- [ ] Kafka retention policy configured
- [ ] TLS 1.3 enabled at ingress/API gateway
- [ ] DICOM PS3.15 de-identification validated
- [ ] OPC-UA certificates installed
- [ ] FHIR endpoint connectivity tested
- [ ] Alembic migrations applied
- [ ] Prometheus metrics visible
- [ ] Grafana dashboards imported
- [ ] k6 load test passed
- [ ] OWASP ZAP / Trivy scan passed
- [ ] UAT sign-off completed

---

## 16. Common Troubleshooting

### Backend cannot connect to PostgreSQL

```bash
docker compose logs postgres
docker compose logs backend
```

Check `DATABASE_URL` in `backend/.env`.

### Kafka connection error

```bash
docker compose logs kafka
docker compose ps kafka
```

For Docker Compose internal networking, use:

```env
KAFKA_BOOTSTRAP_SERVERS=kafka:29092
```

For local host development, use:

```env
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
```

### Frontend cannot reach API

Check Vite proxy in `frontend/vite.config.ts` and API base URL.

### Alembic migration fails

```bash
docker compose exec backend alembic current
docker compose exec backend alembic history
docker compose exec backend alembic upgrade head
```

### Agents do not receive events

Check Kafka topics and consumer groups:

```bash
docker compose logs agent-predictor
docker compose logs agent-scheduler
docker compose logs agent-cost
docker compose logs agent-compliance
```

---

## 17. Recommended Next Steps

1. Replace mock/demo credentials with secure production secrets.
2. Add real DICOM / OPC-UA / FHIR endpoint credentials.
3. Import actual GER2 asset registry data.
4. Train and register the real ONNX RUL model in MLflow.
5. Configure Grafana dashboards for biomedical operations.
6. Run UAT with biomedical engineers and department heads.
7. Execute security hardening before production launch.
