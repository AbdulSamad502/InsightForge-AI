# API Reference

Base URL: http://localhost:8000/api/v1
Auth: Bearer token in Authorization header

## Auth
POST /auth/register  → {token, user}
POST /auth/login     → {token, user}
GET  /auth/me        → {user}

## Datasets
POST /datasets/upload           → {dataset, cleaning_report, suggestions}
GET  /datasets/                 → [{dataset}]
GET  /datasets/{id}/preview     → {columns, rows, total_rows}
POST /datasets/{id}/clean       → {changes_applied, rows_before, rows_after}

## Chat
POST /chat/sessions             → {session}
POST /chat/sessions/{id}/message → {text, chart_data, insight, recommendation}
GET  /chat/sessions/{id}        → {session + messages}

## ML
POST /ml/forecast  → 202 {task_id}
POST /ml/anomaly   → 202 {task_id}
POST /ml/churn     → 202 {task_id}
GET  /ml/results/{task_id} → {status, result_data, chart_data}

## Reports
POST /reports/generate          → 202 {report_id}
GET  /reports/{id}/status       → {status}
GET  /reports/{id}/download     → PDF file

## Dashboard
GET /dashboard/summary          → {kpis, recent_datasets, recent_sessions, recent_reports}