# SecureCoda: Enterprise Activity & Exposure Monitor for Coda

SecureCoda is a full-stack security monitoring, exposure detection, and automated remediation platform designed for collaborative environments powered by **Coda**. Built with **Django (Daphne/ASGI, Django REST Framework, Channels, Celery)** and a **React 18 Dashboard (Bootstrap 5)**.

---

## Table of Contents
1. [Key Features](#key-features)
2. [Project Architecture & How Django Pools Events](#project-architecture--how-django-pools-events)
3. [Database Schema & Models](#database-schema--models)
4. [Celery Background Task Processing](#celery-background-task-processing)
5. [Daphne & ASGI Real-Time WebSockets](#daphne--asgi-real-time-websockets)
6. [Frontend Docker Container Evaluation](#frontend-docker-container-evaluation)
7. [Poetry vs. Pip Usage](#poetry-vs-pip-usage)
8. [API Routes Documentation](#api-routes-documentation)
9. [Project Directory Structure](#project-directory-structure)
10. [Makefile & Quickstart Commands](#makefile--quickstart-commands)
11. [Testing Frameworks (pytest & Jest)](#testing-frameworks-pytest--jest)
12. [Security Features & API Validation](#security-features--api-validation)
13. [Scalability Evaluation](#scalability-evaluation)

---

## Key Features

1. **Robust User Authentication & Activity Logging**:
   - Session/Basic authentication for standard login & registration.
   - **Google Single Sign-On (SSO)** integration via `django-allauth`.
   - Comprehensive **`UserActivityLog`** ledger capturing every user-made change, login/logout, configuration update, scan trigger, and vulnerability status change.
   - **`AuditLog`** compliance tracking recording who resolved which vulnerability, with timestamp, details, and outcome.

2. **Dynamic Secrets Management (`SecretsManager`)**:
   - Class-based singleton (`core.secrets_manager.SecretsManager`).
   - Checks `SECRETS_SOURCE` environment variable:
     - `AWS`: Fetches production credentials from **AWS Secrets Manager** using `boto3`.
     - `LOCAL`: Seamlessly falls back to `secrets.local.json`.

3. **Coda API Token Setup & Inactivity Timeframe**:
   - Configurable Coda API Bearer Key with instant `/whoami` test connection button.
   - Flexible timeframe threshold for unused document detection configurable in **Days**, **Hours**, or **Minutes**.

4. **Real-Time Responsive Dashboard (Bootstrap 5)**:
   - Document preview cards with real-time vulnerability count badges.
   - Sortable & filterable vulnerability inventory (sort by Severity, Title, Category, Document, Detected Date, Status).
   - One-click automated remediation actions:
     - **Redact Sensitive Cell**: Masks PII/credentials with `[REDACTED]`.
     - **Delete Vulnerable Row**: Permanently deletes rows containing sensitive data.
     - **Revoke Permission**: Removes public/external access permissions.
     - **Delete Unused Document**: Archives or deletes stale documents.
   - Real-time live update stream via **Django Channels (WebSockets)** + background dual-mode interval polling without page refresh.

5. **Compliance & Exposure Reporting**:
   - Export security compliance reports in **HTML** or **PDF** format.
   - Saves export configurations in `ExportHistory` with 1-click **Re-Export** functionality.

6. **Slack API Integration (Pending Phase 2)**:
   - Dedicated Slack configuration card marked with **`Pending (Phase 2)`** badge and explanatory note.

---

## Project Architecture & How Django Pools Events

In a synchronous WSGI model, Django handles requests linearly and terminates. For SecureCoda's real-time monitoring and background detection architecture, events are pooled across three coordinated layers:

```
[ Dashboard Client ] <--(WebSocket)-- [ Daphne (ASGI asyncio loop) ] <--(Pub/Sub)-- [ Redis Channel Layer ]
        |                                                                                    ^
        |                                                                                    |
  (HTTP Requests)                                                                     (group_send)
        |                                                                                    |
        v                                                                                    |
 [ Django REST API ]                                                            [ Post-Save Signals / Workers ]
                                                                                             ^
                                                                                             |
[ Celery Beat Scheduler ] --(Task Queue)--> [ Redis Broker ] --(BRPOP)--> [ Celery Worker / Detectors ]
```

1. **ASGI & Django Channels (Daphne + Redis Pub/Sub)**:
   - Daphne runs an asynchronous `asyncio` event loop. Connected dashboard clients maintain persistent WebSocket connections handled by `AlertConsumer`.
   - Redis acts as the Channel Layer (`channels_redis`). When a vulnerability is created, updated, or remediated, Django publishes an event to a Redis group channel via `channel_layer.group_send('alerts_broadcast', ...)`.
   - Daphne's event loop continuously pops and distributes these messages to active client sockets without blocking Django's HTTP workers.

2. **Celery Task Worker Queue Pooling**:
   - Background scans run asynchronously in Celery workers. The workers poll the task broker (Redis) via blocking pop operations (`BRPOP`/`BLPOP`) without keeping Django request threads busy.

3. **Client-Side Event Ingestion & Dual Polling**:
   - The React frontend subscribes to the WebSocket stream for instant push updates and maintains a background interval sync (dual-mode every 20s). This ensures the vulnerability dashboard stays synchronized in real time without requiring a full page refresh.

---

## Database Schema & Models

SecureCoda is backed by relational models with explicit foreign keys and indexing:

- **`User` (django.contrib.auth.models.User)**:
  - Standard user accounts with hashed passwords and profile data.
- **`Document`**:
  - `doc_id` (PK / unique Coda doc ID), `name`, `owner`, `browser_link`, `is_public`, `sharing_status`, `last_modified`, `synced_at`.
- **`Alert`**:
  - `id` (UUID PK), `document` (FK to Document), `title`, `description`, `category` (`sensitive_table`, `sensitive_page`, `public_sharing`, `unused_doc`), `severity` (`critical`, `high`, `medium`, `low`), `status` (`open`, `acknowledged`, `resolved`, `dismissed`), `fingerprint` (unique hash for deduplication), `coda_table_id`, `coda_row_id`, `coda_column_id`, `resolved_by`, `resolved_by_user` (FK to User), `resolved_at`, `detected_at`.
- **`UserActivityLog`**:
  - `id`, `user` (FK to User), `action` (`LOGIN`, `LOGOUT`, `SCAN_TRIGGER`, `ALERT_STATUS_CHANGE`, `CONFIG_UPDATE`, etc.), `description`, `ip_address`, `user_agent`, `details` (JSONField), `timestamp`.
- **`AuditLog`**:
  - `id`, `alert` (FK to Alert), `action_name` (e.g. `redact_row`, `delete_row`), `performed_by` (FK to User), `performed_at`, `parameters` (JSONField), `success` (BooleanField), `result_message`.
- **`ScanConfig`**:
  - Singleton configuration storing `coda_api_token`, `unused_threshold_value`, `unused_threshold_unit` (`days`, `hours`, `minutes`), `scan_interval_minutes`, `slack_webhook_url`, `slack_channel`, `slack_status`.
- **`ExportHistory`**:
  - `id`, `user` (FK to User), `title`, `format` (`html`, `pdf`), `options` (JSONField), `created_at`.

---

## Celery Background Task Processing

Celery offloads resource-intensive and long-running operations from HTTP worker threads:
- **`tasks.run_full_scan`**: Iterates through all Coda documents, executes the detector suite (`UnusedDocumentsDetector`, `PublicSharingDetector`, `SensitiveTableDetector`, `SensitivePageDetector`), deduplicates findings via `fingerprint`, and creates/updates `Alert` records.
- **`tasks.sync_coda_documents`**: Polls Coda REST API `/docs` to discover new or updated documents in the workspace.
- **`Celery Beat`**: Runs periodic scans automatically according to `scan_interval_minutes` defined in `ScanConfig`.

---

## Daphne & ASGI Real-Time WebSockets

- **Why Daphne?**
  - Standard WSGI servers (Gunicorn, uWSGI) only support synchronous request-response lifecycles and cannot maintain long-lived WebSocket connections.
  - Daphne is an ASGI (Asynchronous Server Gateway Interface) reference server written in Python using Twisted/asyncio.
  - It multiplexes both HTTP traffic and WebSocket protocols under a single port (`8000`), routing HTTP to Django's standard view handlers and WebSocket frames to `channels` consumers (`AlertConsumer`).

---

## Frontend Docker Container Evaluation

### Is a Docker container for the frontend necessary?
- **In Development**: **Not strictly necessary**. Running `npm start` natively with Node.js/NVM is faster, provides hot-module replacement (HMR), and consumes fewer system resources.
- **In Production / Orchestration**: **Yes, recommended**. In `docker-compose.yaml`, the frontend is containerized using multi-stage builds (`node:20-alpine` builds static assets, and `nginx:alpine` serves them as an ultra-fast static file server). This isolates dependencies, eliminates environment discrepancies across host operating systems, and allows reverse-proxying API traffic to Daphne.

---

## Poetry vs. Pip Usage

### "Is the project using Poetry or not; if yes, why is requirements.txt also present?"
**Yes, the project is configured for Poetry (`backend/pyproject.toml`) and also provides `backend/requirements.txt`.**

**Why both exist:**
1. **Poetry (`pyproject.toml`)** is the primary dependency and packaging manager. It handles deterministic dependency resolution, virtual environment management, and package metadata.
2. **`requirements.txt`** is provided as a zero-dependency fallback for environments where Poetry is not installed:
   - Minimalist Docker containers or lightweight CI/CD build agents that avoid the installation overhead of Poetry.
   - Developers or systems using standard `pip install -r requirements.txt`.
3. **Smart Makefile**: The root `Makefile` automatically checks if `poetry` is available:
   - If `poetry` is installed, it runs `poetry install`.
   - If `poetry` is not installed, it falls back seamlessly to `pip install -r requirements.txt`.
   - Dedicated explicit targets `make install-poetry` and `make install-pip` are also provided.

---

## API Routes Documentation

The complete REST API and WebSocket specification is documented in [docs/API_ROUTES.md](docs/API_ROUTES.md):
- Authentication & SSO (`/api/auth/`)
- Vulnerability Alerts & Statistics (`/api/alerts/`)
- Coda Documents (`/api/documents/`)
- Automated Remediation Actions & Audit Trail (`/api/remediation/`)
- Security Scanner Engine (`/api/scan/`)
- System Configuration & Token Validation (`/api/config/`)
- Compliance & Exposure Reports (`/api/reports/`)
- Real-Time WebSocket Channel (`/ws/alerts/`)

---

## Project Directory Structure

```
metron-labs/
├── Dockerfile.backend           # Backend Daphne ASGI container definition
├── Dockerfile.frontend          # Multi-stage React + Nginx container definition
├── Makefile                     # Build, test, migration, and run automation
├── README.md                    # Main project documentation & architecture guide
├── docker-compose.yaml          # Multi-container orchestration (local, staging, prod)
├── secrets.local.json           # Local secrets configuration (DB, API Keys, SSO)
├── .nvmrc                       # Node.js version lock (v20.10.0)
│
├── docs/
│   └── API_ROUTES.md            # Detailed REST & WebSocket API specification
│
├── scripts/
│   ├── entrypoint-backend.sh    # Docker container startup script
│   ├── start-local.ps1          # Windows PowerShell local startup script
│   └── start-local.sh           # Unix/Linux/macOS local startup script
│
├── backend/
│   ├── manage.py                # Django management entry point
│   ├── pyproject.toml           # Poetry dependency specification
│   ├── requirements.txt         # Standard pip dependency fallback
│   ├── pytest.ini               # Pytest configuration
│   │
│   ├── alerts/                  # Vulnerability alerts app
│   │   ├── consumers.py         # Django Channels WebSocket consumer
│   │   ├── models.py            # Alert model definition
│   │   ├── serializers.py       # DRF serializers for alerts
│   │   ├── urls.py              # Alert routes (/api/alerts/)
│   │   └── views.py             # AlertViewSet (CRUD, stats, status transitions)
│   │
│   ├── config/                  # Scanner & integration configuration app
│   │   ├── models.py            # ScanConfig model
│   │   ├── serializers.py       # Config serializers
│   │   ├── urls.py              # Config routes (/api/config/)
│   │   └── views.py             # ConfigViewSet (token test, timeframe settings)
│   │
│   ├── core/                    # Core business models, auth, and reports
│   │   ├── activity_logger.py   # ActivityLogger helper for audit trails
│   │   ├── auth_views.py        # Login, Register, Logout, GoogleSSO, Activities
│   │   ├── models.py            # Document, UserActivityLog, AuditLog, ExportHistory
│   │   ├── reports.py           # ReportGenerator (HTML & PDF via ReportLab)
│   │   ├── report_views.py      # ReportViewSet (export, re-export, history)
│   │   ├── secrets_manager.py   # SecretsManager singleton (AWS + local JSON)
│   │   └── views.py             # DocumentViewSet, AuditLogViewSet
│   │
│   ├── remediation/             # Automated remediation engine
│   │   ├── actions/             # Pluggable remediation actions
│   │   │   ├── base.py          # BaseAction ABC
│   │   │   ├── redact_row.py    # Redacts sensitive cell values
│   │   │   ├── delete_row.py    # Deletes vulnerable Coda row
│   │   │   ├── revoke_permission.py # Revokes public link sharing
│   │   │   └── delete_document.py   # Deletes or archives document
│   │   ├── views.py             # RemediationViewSet & AuditLogViewSet
│   │   └── urls.py              # Remediation routes (/api/remediation/)
│   │
│   ├── scanner/                 # Coda detection engine & detectors
│   │   ├── coda_client.py       # Coda REST API v1 client wrapper
│   │   ├── detectors/           # Security vulnerability detectors
│   │   │   ├── unused_docs.py   # Flags inactive docs by configured timeframe
│   │   │   ├── public_sharing.py# Identifies public document exposures
│   │   │   ├── sensitive_table.py# Scans grid rows for PII/credentials
│   │   │   └── sensitive_page.py # Scans canvas content for secrets
│   │   ├── tasks.py             # Celery async tasks (run_full_scan, sync)
│   │   └── views.py             # ScanViewSet (manual trigger, status, history)
│   │
│   ├── securecoda/              # Django project core configuration
│   │   ├── asgi.py              # ASGI routing (Daphne + Channels)
│   │   ├── celery.py            # Celery app initialization
│   │   ├── settings.py          # Django settings with SecretsManager integration
│   │   └── urls.py              # Root URL dispatcher
│   │
│   └── tests/                   # Backend test suite
│       ├── conftest.py          # Pytest fixtures and mock Coda data
│       ├── factories.py         # Factory Boy test models
│       ├── fixtures/            # Sample Coda API response JSON fixtures
│       ├── test_api_and_remediation.py # Django unit tests
│       ├── test_auth_and_secrets.py    # Auth, SSO & SecretsManager tests
│       ├── test_pytest_suite.py        # Pytest-native tests
│       └── test_reports_and_export.py  # HTML/PDF export & history tests
│
└── frontend/
    ├── package.json             # React dependencies & scripts
    ├── .nvmrc                   # Node version lock
    ├── src/
    │   ├── App.js               # Main Dashboard application component
    │   ├── components/          # Reusable Bootstrap 5 components
    │   │   ├── ActivityLogModal.jsx    # User activity history modal
    │   │   ├── AuthModal.jsx           # Sign-in, Sign-up & Google SSO modal
    │   │   ├── DocumentPreview.jsx     # Monitored Coda document cards
    │   │   ├── ExportModal.jsx         # HTML/PDF export & re-export modal
    │   │   ├── Navbar.jsx              # Header, scan trigger & profile dropdown
    │   │   ├── RemediationModal.jsx    # Action confirmation & execution modal
    │   │   ├── SettingsModal.jsx       # Coda API key, timeframe & Slack status
    │   │   ├── StatsCards.jsx          # Metric counters & summary badges
    │   │   └── VulnerabilityTable.jsx  # Sortable & filterable exposure table
    │   ├── hooks/
    │   │   └── useWebSocket.js         # Auto-reconnecting WebSocket hook
    │   ├── services/
    │   │   └── api.js                  # Centralized REST API client
    │   └── __tests__/
    │       └── DashboardComponents.test.jsx # React Jest component tests
```

---

## Makefile & Quickstart Commands

```bash
# View all available targets
make help

# Install dependencies (auto-detects Poetry or Pip, plus npm)
make install

# Explicit package manager installs
make install-poetry
make install-pip

# Run development servers
make run-backend      # Runs Daphne/Django ASGI server on http://localhost:8000
make run-frontend     # Runs React dev server on http://localhost:3000

# Execute database migrations
make makemigrations
make migrate

# Run tests
make test             # Runs both backend & frontend test suites
make test-pytest      # Runs backend pytest suite with fixtures
make test-frontend    # Runs React Jest test suite

# Docker operations
make docker-up        # Builds and launches all containers in background
make docker-down      # Stops and removes all containers
make clean            # Cleans up __pycache__ and build artifacts
```

---

## Testing Frameworks (pytest & Jest)

### Backend: `pytest` & `pytest-django`
- Configured in `backend/pytest.ini`.
- Uses `factory-boy` and `faker` in `backend/tests/factories.py` to generate realistic mock documents, users, and alerts.
- Fixtures in `backend/tests/conftest.py` load sample Coda API JSON mocks (`sample_coda_docs.json`).
- Run:
  ```bash
  pytest backend/tests
  ```
  *(17/17 tests passing)*

### Frontend: `Jest` & `@testing-library/react`
- Tests located in `frontend/src/__tests__/DashboardComponents.test.jsx`.
- Tests verify:
  - Metric calculation in `StatsCards`.
  - Document rendering and vulnerability count badges in `DocumentPreview`.
  - Column sorting, searching, and category filter pills in `VulnerabilityTable`.
  - Sign In, Sign Up, and Google SSO tabs in `AuthModal`.
  - Coda API Key test validation and Slack Phase 2 badge in `SettingsModal`.
- Run:
  ```bash
  cd frontend && npm test -- --watchAll=false
  ```
  *(5/5 component test suites passing)*

---

## Security Features & API Validation

1. **Authentication & Authorization**:
   - Session authentication with CSRF tokens for all state-mutating requests (`POST`, `PUT`, `DELETE`).
   - Secure Google SSO token validation via `django-allauth`.
2. **Secrets Protection**:
   - Zero hardcoded credentials in codebase.
   - Dual-source `SecretsManager` fetches credentials from AWS Secrets Manager in production, falling back to local gitignored JSON.
3. **Data Sanitization & Fingerprinting**:
   - SHA-256 fingerprinting on alert parameters prevents duplicate alert flooding.
   - Redaction actions replace live PII with masked tokens directly in Coda tables.
4. **Input Validation**:
   - DRF Serializers validate all incoming request payloads (`AlertStatusUpdateSerializer`, `ScanConfigSerializer`, etc.).
   - Explicit parameter checking on timeframe thresholds (minimum values, allowed unit strings: `days`, `hours`, `minutes`).
5. **Immutable Audit Trails**:
   - `UserActivityLog` records every login, configuration change, and scan trigger.
   - `AuditLog` records every remediation action taken, the invoking user ID, timestamp, and result status.

---

## Scalability Evaluation

- **Horizontally Scalable WebSocket Ingestion**: Using `channels_redis`, multiple Daphne instances can run behind an AWS Application Load Balancer / Nginx reverse proxy. Redis handles pub/sub message distribution across all server instances.
- **Asynchronous Task Offloading**: Long-running Coda API scans never block the web tier. Celery workers can be scaled independently on dedicated compute nodes (e.g. AWS ECS / Kubernetes pods) to handle larger workspaces.
- **Database Indexing & Query Optimization**:
  - `Alert.fingerprint` and `Document.doc_id` are indexed for fast deduplication lookups.
  - ViewSets leverage `select_related('document')` to avoid N+1 query bottlenecks.
- **Dual-Mode Sync Resilience**: WebSocket live updates combined with fallback interval polling ensure reliable state synchronization even in environments with intermittent network drops or strict firewalls.
