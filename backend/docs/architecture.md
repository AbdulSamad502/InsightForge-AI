# Architecture Overview

## System Design

Frontend (Streamlit) → FastAPI Backend → PostgreSQL
                              ↓
                    LangChain AgentExecutor
                              ↓
                    Groq LLM (llama-3.3-70b)
                              ↓
                    Tools: Pandas | Chart | ML | Insight
                              ↓
                    LangGraph (Report Pipeline)

## Key Decisions

**LangChain for chat, LangGraph for reports:**
Chat is a tool-calling loop (AgentExecutor fits perfectly).
Reports are a DAG with conditional branches (StateGraph fits perfectly).

**Streamlit now, React later:**
All business logic is in FastAPI services.
Streamlit is pure display layer. Swap to React = rewrite only UI.
api_client.py methods map 1:1 to React fetch() calls.

**Background tasks for ML and reports:**
These operations take 10-60 seconds. FastAPI BackgroundTasks
returns 202 immediately. Frontend polls for completion.