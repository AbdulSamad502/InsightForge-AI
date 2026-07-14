# 🤖 AI Data Analyst Agent
### AI-powered Business Intelligence Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-0.3.1-1C3C3C?style=flat)](https://langchain.com)
[![LangGraph](https://img.shields.io/badge/LangGraph-0.2.28-FF6B6B?style=flat)](https://langchain.com/langgraph)
[![Groq](https://img.shields.io/badge/Groq-llama--3.3--70b-F55036?style=flat)](https://groq.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat&logo=postgresql)](https://postgresql.org)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat&logo=docker)](https://docker.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.39-FF4B4B?style=flat&logo=streamlit)](https://streamlit.io)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python)](https://python.org)

**🌐 Live Demo:** [your-app.streamlit.app](https://your-app.streamlit.app)
**📹 Demo Video:** [Watch 3-minute demo](https://youtube.com/your-demo-link)
**📖 API Docs:** [your-api.onrender.com/docs](https://your-api.onrender.com/docs)

---

## What Is This?

Most businesses have data but can't analyze it. Hiring a data analyst costs $50,000+/year.
This platform lets any business owner upload their Excel/CSV data, ask questions in plain
English, and get instant charts, forecasts, anomaly alerts, and professional PDF reports —
no SQL, no Python, no BI tools required.

Think: **ChatGPT + Power BI + Data Analyst**, available 24/7 for any file you upload.

---

## Demo

> **Upload** → **Ask** → **Get Charts + Insights + Forecasts + PDF Report**

![Dashboard Screenshot](docs/screenshots/dashboard.png)
![Chat Screenshot](docs/screenshots/chat.png)
![Report Screenshot](docs/screenshots/report.png)

---

## Features

### ✅ V1.0 (Implemented)

**Data Management**
- CSV and Excel (.xlsx) upload with automatic profiling
- Smart data cleaning: missing values, duplicates, negatives, bad dates, inconsistent categories
- AI-generated smart questions based on your actual column names

**AI Chat**
- Natural language → pandas code → chart → business insight → recommendation
- Intent classifier routes questions to the right tool automatically
- Conversation memory (last 10 turns per session)
- 6 chart types: bar, line, pie, heatmap, histogram, scatter
- "Explain this chart" button for every visualization

**Machine Learning**
- Sales/Revenue Forecasting (GradientBoosting + bootstrap confidence intervals)
- Anomaly Detection (IQR + IsolationForest + highlighted visualization)
- Churn Prediction (RandomForest + feature importance analysis)
- Background task processing — results polled in real-time

**Reports**
- LangGraph 5-node pipeline: gather → ML → charts → summary → PDF
- Professional PDF: cover page, executive summary, data overview, insights, charts, ML results, recommendations
- One-click generation and download

**Platform**
- JWT authentication
- Dashboard with KPI cards and recent activity
- LangSmith observability — every LLM call traced
- Docker + Docker Compose deployment
- CI/CD via GitHub Actions (lint + test + docker build)

### 🗺️ V2 Roadmap

- [ ] React + TypeScript frontend (zero backend changes — architecture is ready)
- [ ] MySQL/PostgreSQL direct connection with NL-to-SQL
- [ ] Multi-dataset cross-analysis with auto join detection
- [ ] Scheduled automated reports via email
- [ ] Team workspaces with role-based access control
- [ ] Redis caching for repeated queries
- [ ] Celery for distributed ML job processing
- [ ] Customer segmentation (K-Means clustering)
- [ ] Multi-agent LangGraph architecture for complex queries

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Streamlit (React-ready architecture) |
| Backend | FastAPI + Pydantic v2 + SQLAlchemy |
| Database | PostgreSQL + Alembic migrations |
| AI Agent | LangChain AgentExecutor + Groq (llama-3.3-70b) |
| Report Pipeline | LangGraph StateGraph (5 nodes) |
| ML Models | Scikit-learn (GradientBoosting, IsolationForest, RandomForest) |
| Charts | Plotly |
| PDF Generation | ReportLab |
| Observability | LangSmith |
| Auth | JWT (python-jose + passlib/bcrypt) |
| Deployment | Docker + Render + Streamlit Cloud |
| CI/CD | GitHub Actions |

---

## Architecture
Frontend (Streamlit)
↓ HTTP (all business logic in backend)
FastAPI Backend (/api/v1/)
├── Auth Module
├── Datasets Module (upload, clean, profile)
├── Chat Module → LangChain AgentExecutor
│       ↓
│   Intent Classifier (llama-8b, fast)
│       ↓
│   Tools: PandasTool | ChartTool | MLTool | InsightTool
│       ↓
│   Groq LLM (llama-3.3-70b)
├── ML Module (forecast/anomaly/churn) → Background Tasks
├── Reports Module → LangGraph Pipeline
│       Nodes: gather_insights → check_ml → generate_charts
│              → write_summary → compile_pdf
├── Visualization Module (6 chart builders)
└── Dashboard Module
↓
PostgreSQL (users, datasets, chat, ml_results, reports)

**Key architectural decisions:**
- All business logic in FastAPI — Streamlit is pure display (swap to React = UI rewrite only)
- LangChain for chat (tool-calling loop), LangGraph for reports (conditional DAG)
- Background tasks for ML + reports — returns 202 immediately, frontend polls
- Feature-based folder structure: each module has router/service/repository/schemas/models

---

## Quick Start

```bash
# 1. Clone and setup
git clone https://github.com/YOUR_USERNAME/ai-data-analyst.git
cd ai-data-analyst
cp backend/.env.example backend/.env
# Fill in GROQ_API_KEY and LANGCHAIN_API_KEY in backend/.env

# 2. Start everything
docker-compose up --build

# 3. Run database migrations
docker-compose exec api alembic upgrade head

# Open http://localhost:8501 in your browser
```

**Get your free API keys:**
- Groq (LLM): https://console.groq.com (free, no credit card)
- LangSmith (observability): https://smith.langchain.com (free tier)

---

## Project Structure
ai-data-analyst/
├── backend/
│   ├── app/
│   │   ├── modules/          # Feature-based: auth, datasets, chat, ml, reports
│   │   ├── ai/               # Agent, tools, LangGraph pipeline, prompts
│   │   ├── core/             # Config, security, exceptions, middleware
│   │   └── shared/           # Dependencies, pagination, responses
│   ├── tests/                # 38 tests: unit + API
│   ├── docs/                 # PRD, architecture, API reference, deployment
│   └── alembic/              # Database migrations
└── frontend/
├── pages/                # Upload, Chat, Dashboard, Reports
├── components/           # Reusable UI components
└── utils/                # API client (maps 1:1 to React fetch calls)
---

## Running Tests

```bash
cd backend
venv\Scripts\activate  # Windows
pytest tests/ -v       # runs 38 tests
```

---

## Deployment

See [docs/deployment.md](backend/docs/deployment.md) for step-by-step instructions.

**Live deployment:**
- Backend: Render (FastAPI + PostgreSQL, free tier)
- Frontend: Streamlit Community Cloud (free)

---

## Built With

This project demonstrates production-quality AI engineering:
- **Sandboxed code execution** — pandas tool blocks dangerous imports
- **Token optimization** — minimal prompts, key rotation, simple-answer bypass
- **Observability** — LangSmith traces every LLM call with latency and token usage
- **Background tasks** — ML and report generation don't block HTTP responses
- **Repository pattern** — clean separation of business logic from data access
- **Feature-based architecture** — each module is self-contained and independently testable

---

## Author

**Abdul Samad**
- Portfolio: [your-portfolio.com]
- LinkedIn: [linkedin.com/in/your-profile]
- GitHub: [github.com/your-username]

*Built as part of a 7-day AI engineering sprint — demonstrating industrial-level
architecture, not just prototype-level coding.*