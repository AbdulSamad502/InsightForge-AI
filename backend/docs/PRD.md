FILE 15-18: DOCS FOLDER

File: backend/docs/PRD.md

markdown# Product Requirements Document
## AI Data Analyst Agent — V1.0

### Problem Statement
Small and medium businesses have data but lack the technical skills to analyze it.
Hiring a data analyst costs $50,000+/year. This platform delivers instant AI-powered
analysis for a fraction of the cost.

### V1 Features (Implemented)
- CSV/XLSX upload with auto-profiling
- Smart data cleaning (5 issue types)
- AI chat with pandas agent (NL → analysis → chart → insight)
- 6 chart types (bar, line, pie, heatmap, histogram, scatter)
- Business insight + recommendation per response
- Forecasting (GradientBoosting + confidence intervals)
- Anomaly detection (IQR + IsolationForest)
- Churn prediction (RandomForest + feature importance)
- LangGraph report pipeline → professional PDF
- Dashboard with KPIs and recent activity
- JWT authentication
- Docker deployment
- LangSmith observability

### V2 Roadmap
- React + TypeScript frontend (zero backend changes)
- MySQL/PostgreSQL direct connection (NL-to-SQL)
- Multi-dataset cross-analysis
- Scheduled automated reports via email
- Team workspaces with role-based access
- Redis caching for repeated queries
- Celery for distributed ML jobs
- Customer segmentation (K-Means)
- Multi-agent LangGraph architecture

