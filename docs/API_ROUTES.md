# SecureCoda API Reference & Routes Documentation

SecureCoda provides a comprehensive RESTful API alongside real-time WebSocket streams for continuous security monitoring, exposure detection, and automated remediation across Coda collaborative documents.

---

## Base URLs
- **REST API Base URL**: `http://localhost:8000/api/` (or relative path `/api/`)
- **WebSocket Base URL**: `ws://localhost:8000/ws/`

---

## Authentication & Security Model
All requests utilize Django standard session authentication or token headers with CSRF protection:
- Header: `X-CSRFToken: <csrf-token>`
- Cookie: `csrftoken=<token>; sessionid=<session-id>`
- Credentials: `include` (Fetch / Axios)

Endpoints enforce permission checks (`AllowAny` for public/read-only views with user context capture, `IsAuthenticated` for write/remediation actions). User activities and audit trails are automatically recorded with user ID, IP address, user-agent, and event timestamps.

---

## 1. Authentication Endpoints (`/api/auth/`)

### Register User
- **Route**: `POST /api/auth/register/`
- **Description**: Registers a new user account and creates a session.
- **Request Body**:
```json
{
  "username": "secops_analyst",
  "email": "analyst@example.com",
  "password": "SecurePassword123!"
}
```
- **Response** (`201 Created`):
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "secops_analyst",
    "email": "analyst@example.com"
  }
}
```

### Login
- **Route**: `POST /api/auth/login/`
- **Description**: Authenticates user via username or email and starts a session.
- **Request Body**:
```json
{
  "username": "secops_analyst",
  "password": "SecurePassword123!"
}
```
- **Response** (`200 OK`):
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "secops_analyst",
    "email": "analyst@example.com"
  }
}
```

### Logout
- **Route**: `POST /api/auth/logout/`
- **Description**: Invalidates the active session and logs the activity.
- **Response** (`200 OK`):
```json
{
  "message": "Logged out successfully"
}
```

### Current User / Status
- **Route**: `GET /api/auth/me/` (alias: `GET /api/auth/status/`)
- **Description**: Retrieves current authenticated user context and role.
- **Response** (`200 OK`):
```json
{
  "authenticated": true,
  "user": {
    "id": 1,
    "username": "secops_analyst",
    "email": "analyst@example.com",
    "is_staff": false
  }
}
```

### Google Single Sign-On (SSO)
- **Route**: `POST /api/auth/google/`
- **Description**: Authenticates or provisions a user using Google OAuth ID credentials.
- **Request Body**:
```json
{
  "email": "user@domain.com",
  "name": "Security User",
  "google_id": "10492817281928"
}
```
- **Response** (`200 OK`):
```json
{
  "message": "Google SSO login successful",
  "user": {
    "id": 2,
    "username": "user@domain.com",
    "email": "user@domain.com"
  }
}
```

### User Activity Logs
- **Route**: `GET /api/auth/activities/`
- **Description**: Returns paginated audit logs of user actions (logins, status changes, configuration updates, remediation).
- **Query Parameters**:
  - `page`: Page number (default: 1)
  - `action`: Filter by action type (`LOGIN`, `LOGOUT`, `SCAN_TRIGGER`, `ALERT_STATUS_CHANGE`, `CONFIG_UPDATE`)
- **Response** (`200 OK`):
```json
{
  "count": 42,
  "results": [
    {
      "id": 1,
      "user_username": "secops_analyst",
      "action": "ALERT_STATUS_CHANGE",
      "description": "Alert 'Public Shared Doc' status changed from open to acknowledged",
      "ip_address": "127.0.0.1",
      "timestamp": "2026-09-23T06:14:00Z",
      "details": {
        "alert_id": "92dae42b-58bb-4bc4-bcf2-b88d01111977",
        "from_status": "open",
        "to_status": "acknowledged"
      }
    }
  ]
}
```

---

## 2. Alerts & Vulnerabilities (`/api/alerts/`)

### List Vulnerabilities
- **Route**: `GET /api/alerts/`
- **Description**: Retrieves monitored security exposure alerts with sorting, searching, and filtering.
- **Query Parameters**:
  - `category`: Filter by category (`sensitive_table`, `sensitive_page`, `public_sharing`, `unused_doc`)
  - `severity`: Filter by severity (`critical`, `high`, `medium`, `low`)
  - `status`: Filter by status (`open`, `acknowledged`, `resolved`, `dismissed`)
  - `document__doc_id`: Filter by Coda document ID
  - `search`: Search keyword matching title, description, document name, or fingerprint
  - `ordering`: Sort field (e.g. `-detected_at`, `severity`, `title`, `status`)
- **Response** (`200 OK`):
```json
{
  "count": 8,
  "results": [
    {
      "id": "e2da42e3-6ce7-4ee2-b430-c3d3ff69f0e1",
      "document": {
        "id": "d-abc123xyz",
        "name": "Q3 Financials & PII Vault"
      },
      "category": "sensitive_table",
      "severity": "critical",
      "status": "open",
      "title": "Unmasked Credit Card Number Found",
      "description": "Table 'Customers', Column 'CardNumber' contains 14 raw PCI-DSS violations.",
      "coda_table_id": "grid-789",
      "coda_row_id": "i-row456",
      "coda_column_id": "c-col123",
      "detected_at": "2026-09-23T06:00:00Z"
    }
  ]
}
```

### Aggregate Statistics
- **Route**: `GET /api/alerts/stats/`
- **Description**: Returns real-time aggregate counts for dashboard metrics cards.
- **Response** (`200 OK`):
```json
{
  "total_alerts": 12,
  "open_alerts": 7,
  "critical_alerts": 2,
  "high_alerts": 3,
  "medium_alerts": 2,
  "low_alerts": 0,
  "by_category": [
    { "category": "sensitive_table", "total": 5, "open": 3, "resolved": 2 },
    { "category": "public_sharing", "total": 4, "open": 2, "resolved": 2 },
    { "category": "unused_doc", "total": 3, "open": 2, "resolved": 1 }
  ],
  "by_severity": [
    { "severity": "critical", "count": 2 },
    { "severity": "high", "count": 3 },
    { "severity": "medium", "count": 2 }
  ]
}
```

### Update Alert Status
- **Route**: `POST /api/alerts/{id}/status/` (or `PATCH /api/alerts/{id}/status/`)
- **Description**: Changes vulnerability workflow status (`open`, `acknowledged`, `resolved`, `dismissed`).
- **Request Body**:
```json
{
  "status": "acknowledged"
}
```
- **Response** (`200 OK`): Full updated `Alert` object.

---

## 3. Documents API (`/api/documents/`)

### List Monitored Documents
- **Route**: `GET /api/documents/`
- **Description**: Lists all tracked Coda documents with vulnerability counts and metadata.
- **Response** (`200 OK`):
```json
{
  "count": 5,
  "results": [
    {
      "doc_id": "d-abc123xyz",
      "name": "Q3 Financials & PII Vault",
      "owner": "coda_admin@metronlabs.com",
      "browser_link": "https://coda.io/d/_dabc123xyz",
      "sharing_status": "anyoneWithLink",
      "is_public": true,
      "updated_at": "2026-09-22T14:30:00Z",
      "vulnerability_count": 3
    }
  ]
}
```

### Synchronize Documents
- **Route**: `POST /api/documents/sync/`
- **Description**: Triggers an on-demand sync of Coda workspace document inventory.
- **Response** (`200 OK`):
```json
{
  "message": "Document sync initiated",
  "status": "success"
}
```

---

## 4. Remediation Actions (`/api/remediation/`)

### List Applicable Actions
- **Route**: `GET /api/remediation/actions/?category={category}`
- **Description**: Returns all remediation actions supported for a given vulnerability type.
- **Response** (`200 OK`):
```json
{
  "category": "sensitive_table",
  "actions": [
    {
      "name": "redact_row",
      "display_name": "Redact Row Values",
      "description": "Replaces exposed PII / sensitive column cells with [REDACTED]."
    },
    {
      "name": "delete_row",
      "display_name": "Delete Table Row",
      "description": "Permanently deletes the row containing the exposure from the Coda table."
    }
  ]
}
```

### Execute Remediation
- **Route**: `POST /api/remediation/execute/`
- **Description**: Executes an automated remediation action on Coda and records an immutable audit log.
- **Request Body**:
```json
{
  "alert_id": "e2da42e3-6ce7-4ee2-b430-c3d3ff69f0e1",
  "action_name": "redact_row",
  "parameters": {}
}
```
- **Response** (`200 OK`):
```json
{
  "success": true,
  "message": "Sensitive cells in row i-row456 successfully redacted.",
  "audit_log_id": 84,
  "status": "resolved"
}
```

### Audit Log History
- **Route**: `GET /api/remediation/audit-log/`
- **Description**: Immutable ledger of remediation actions executed by users.
- **Response** (`200 OK`):
```json
{
  "count": 15,
  "results": [
    {
      "id": 84,
      "alert_id": "e2da42e3-6ce7-4ee2-b430-c3d3ff69f0e1",
      "action_name": "redact_row",
      "performed_by": "secops_analyst",
      "performed_at": "2026-09-23T06:45:00Z",
      "success": true,
      "result_message": "Sensitive cells in row i-row456 successfully redacted."
    }
  ]
}
```

---

## 5. Security Scanner Engine (`/api/scan/`)

### Trigger Manual Scan
- **Route**: `POST /api/scan/trigger/`
- **Description**: Triggers an asynchronous vulnerability scan across all Coda documents.
- **Response** (`202 Accepted`):
```json
{
  "message": "Security scan task dispatched",
  "task_id": "celery-task-9a7f3e2b"
}
```

### Scan Status
- **Route**: `GET /api/scan/status/`
- **Description**: Checks current scanner status, active Celery tasks, and last completed scan timestamp.
- **Response** (`200 OK`):
```json
{
  "is_scanning": false,
  "last_scan_at": "2026-09-23T06:30:00Z",
  "last_scan_duration_seconds": 4.2
}
```

### Scan History
- **Route**: `GET /api/scan/history/`
- **Description**: Returns recent scan execution summaries and findings count.

---

## 6. System Configuration (`/api/config/`)

### Get Current Configuration
- **Route**: `GET /api/config/`
- **Description**: Returns scanner parameters, threshold configs, and integration status.
- **Response** (`200 OK`):
```json
{
  "coda_token_configured": true,
  "unused_threshold_value": 90,
  "unused_threshold_unit": "days",
  "scan_interval_minutes": 60,
  "slack_status": "pending"
}
```

### Update Configuration
- **Route**: `PUT /api/config/` (or `PATCH /api/config/`)
- **Description**: Updates unused document threshold, time units (`days`, `hours`, `minutes`), and Coda API token.
- **Request Body**:
```json
{
  "coda_api_token": "coda-api-token-value",
  "unused_threshold_value": 30,
  "unused_threshold_unit": "days"
}
```
- **Response** (`200 OK`):
```json
{
  "message": "Configuration updated successfully",
  "config": {
    "unused_threshold_value": 30,
    "unused_threshold_unit": "days"
  }
}
```

### Validate Coda API Token
- **Route**: `POST /api/config/validate-token/`
- **Description**: Tests a Coda API token against the live Coda `/whoami` endpoint without saving.
- **Request Body**:
```json
{
  "token": "test-coda-api-token"
}
```
- **Response** (`200 OK`):
```json
{
  "valid": true,
  "name": "SecOps Admin",
  "scoped_email": "admin@company.com"
}
```

### Slack Integration Status
- **Route**: `GET /api/config/slack-status/`
- **Description**: Returns Phase 2 Slack notification integration status.
- **Response** (`200 OK`):
```json
{
  "status": "pending",
  "phase": "Phase 2",
  "message": "Slack API alerting integration is scheduled for Phase 2."
}
```

---

## 7. Compliance & Exposure Reports (`/api/reports/`)

### Export Report (HTML or PDF)
- **Route**: `POST /api/reports/export/`
- **Description**: Generates and downloads a compliance and exposure audit report in **HTML** or **PDF** format.
- **Request Body**:
```json
{
  "format": "pdf",
  "title": "Q3 Coda Compliance Audit",
  "options": {
    "category": "all",
    "severity": "high",
    "include_audit_trail": true
  }
}
```
- **Response**:
  - `Content-Type`: `application/pdf` or `text/html; charset=utf-8`
  - `Content-Disposition`: `attachment; filename="securecoda-report.pdf"`

### View Export History
- **Route**: `GET /api/reports/history/`
- **Description**: Returns previously used export configurations for 1-click re-exports.
- **Response** (`200 OK`):
```json
[
  {
    "id": 1,
    "title": "Q3 Coda Compliance Audit",
    "format": "pdf",
    "options": {
      "category": "all",
      "severity": "high",
      "include_audit_trail": true
    },
    "created_at": "2026-09-23T06:40:00Z"
  }
]
```

### Re-Export from History
- **Route**: `POST /api/reports/{id}/re-export/`
- **Description**: Immediately re-generates an export using previously saved options and returns the file download.
- **Request Body**:
```json
{
  "format": "html"
}
```
- **Response**: Binary or text attachment file stream.

---

## 8. Real-Time WebSocket Channel (`/ws/alerts/`)

- **URL**: `ws://localhost:8000/ws/alerts/`
- **Protocol**: Django Channels ASGI with Daphne and Redis channel layers.
- **Server Push Events**:
  - `ALERT_CREATED`: Pushed when a scanner detector identifies a new exposure.
  - `ALERT_UPDATED`: Pushed when status is changed or remediation resolves an issue.
  - `SCAN_STARTED`: Pushed when security scan begins.
  - `SCAN_COMPLETED`: Pushed when security scan finishes.

**Sample WebSocket Payload**:
```json
{
  "event": "ALERT_CREATED",
  "data": {
    "id": "e2da42e3-6ce7-4ee2-b430-c3d3ff69f0e1",
    "title": "Unmasked Credit Card Number Found",
    "severity": "critical",
    "category": "sensitive_table",
    "document_name": "Q3 Financials & PII Vault"
  }
}
```
