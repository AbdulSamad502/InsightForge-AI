# Deployment Guide

## Local Development
1. cp backend/.env.example backend/.env  (fill API keys)
2. docker-compose up db -d
3. cd backend && alembic upgrade head
4. uvicorn app.main:app --reload --port 8000
5. cd frontend && streamlit run app.py

## Production (Render + Streamlit Cloud)
1. Push code to GitHub
2. Render: New Web Service → connect repo → backend/
   Set env vars: DATABASE_URL, GROQ_API_KEY, SECRET_KEY, LANGCHAIN_API_KEY
3. Render: New PostgreSQL → copy DATABASE_URL
4. Streamlit Community Cloud: New app → frontend/app.py
   Set secret: BACKEND_URL = your Render URL