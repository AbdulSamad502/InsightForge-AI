# ⚡ InsightForge-AI

<div align="center">

## AI-Powered Business Intelligence Platform

Transform raw business data into actionable insights using **Generative AI, Machine Learning, and Agentic AI workflows**.

Upload datasets, ask questions in natural language, generate visualizations, predictions, and business reports — without writing SQL or Python.

</div>

---

# 📸 Screenshots

## Dashboard

<img width="1912" height="915" alt="image" src="https://github.com/user-attachments/assets/e2fd99ec-6eb2-46be-9866-2d90d6d9833a" />



---

# 📌 Overview

Businesses generate large amounts of data, but extracting meaningful insights often requires technical expertise, dedicated analysts, and time-consuming reporting workflows.

**InsightForge-AI bridges this gap by providing an AI-powered data analyst assistant that automates repetitive analytics tasks.**

Instead of spending hours cleaning datasets, creating charts, and preparing reports, users can interact with their data using simple natural language questions.

Example:

```
User:
"Why did sales decrease last month?"

InsightForge AI:

✓ Analyzes the dataset
✓ Finds important patterns
✓ Generates visualization
✓ Explains business insights
✓ Provides recommendations
```

---
## AI Data Analyst Chat

<img width="1896" height="867" alt="image" src="https://github.com/user-attachments/assets/7227f825-9b32-4041-91ea-60a0dfbe0b9d" />


# 🚀 Business Impact

InsightForge-AI helps organizations:

- Reduce time spent on repetitive data analysis
- Minimize manual reporting efforts
- Enable non-technical users to explore business data
- Accelerate decision-making through AI-powered insights

Professional data analysis often requires dedicated analysts, BI tools, and significant operational investment.

InsightForge-AI helps reduce the workload of repetitive analytical tasks by automating:

- Dataset exploration
- Data cleaning assistance
- Visualization generation
- Business question answering
- Report creation
- ML-based predictions

The goal is not to replace analysts, but to **increase productivity and allow teams to focus on strategic decisions.**

---

# ✨ Features

## 📂 Smart Data Analysis

- Upload CSV and Excel datasets
- Automatic dataset profiling
- Column type detection
- Missing value analysis
- Duplicate detection
- Data cleaning assistance
- AI-generated analytical questions


---

## 🤖 AI Data Analyst Agent

Ask business questions naturally:

```
"Show monthly revenue trends"

"Find top performing products"

"Predict next quarter sales"

"Detect unusual transactions"
```

The AI agent:

- Understands user intent
- Selects appropriate tools
- Performs analysis
- Generates insights
- Provides recommendations


---

## 📊 Visualization Engine

Automatically creates:

- Bar charts
- Line charts
- Pie charts
- Heatmaps
- Histograms
- Scatter plots


Each visualization includes:

- Data explanation
- Business interpretation
- Actionable insights


---

## 🤖 Machine Learning Capabilities

Integrated ML modules:

### Sales Forecasting

Predict future sales trends for planning and decision-making.

### Anomaly Detection

Identify unusual patterns and potential data issues.

### Customer Churn Prediction

Detect customers with higher churn probability.


## Machine Learning Predictions

<img width="1896" height="926" alt="image" src="https://github.com/user-attachments/assets/97902865-ad90-42b4-8334-37e71c21f796" />

---

## 📄 AI Report Generation

Generate professional PDF reports containing:

- Executive summary
- Dataset overview
- Key insights
- Visualizations
- ML results
- Recommendations

## Generated Business Report

<img width="1917" height="891" alt="image" src="https://github.com/user-attachments/assets/33a58d9d-a647-47e3-b737-69937649ec27" />


---

# 🧠 AI Architecture

```
                User Question

                      ↓

              Intent Classifier

                      ↓

              AI Agent (LangChain)

                      ↓

        ------------------------------

        Data Analysis Tool

        Visualization Tool

        Machine Learning Tool

        ------------------------------

                      ↓

        Business Insight + Recommendation
```

Report generation uses **LangGraph workflow pipelines** for structured AI execution.

---

# 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + TypeScript + Tailwind CSS |
| Backend | FastAPI + Python |
| Database | PostgreSQL + SQLAlchemy |
| AI Framework | LangChain + LangGraph |
| Local LLM | Ollama |
| Machine Learning | Scikit-learn |
| Visualization | Plotly |
| Authentication | JWT + bcrypt |
| Deployment | Docker + Docker Compose |
| Testing | Pytest |


---

# 📁 Project Structure

```text
InsightForge-AI/

├── backend/
│   ├── app/
│   │   ├── modules/
│   │   ├── ai/
│   │   ├── core/
│   │   └── database/
│   │
│   └── tests/

├── frontend-react/
│   ├── src/
│   ├── components/
│   └── pages/

├── docs/
│   └── screenshots/

├── docker-compose.yml
└── README.md
```

---

# 🚀 Installation & Setup

## 1. Clone Repository

```bash
git clone https://github.com/AbdulSamad502/InsightForge-AI.git

cd InsightForge-AI
```

---

# Backend Setup

```bash
cd backend

python -m venv venv
```

Activate environment:

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

---

# 🔑 Environment Configuration

Create a `.env` file inside the backend folder:

```
backend/.env
```

Add your configuration:

```env
DATABASE_URL=postgresql://username:password@localhost:5432/insightforge

SECRET_KEY=your_secret_key


# LLM Provider

LLM_PROVIDER=ollama


# Ollama Local Model

OLLAMA_BASE_URL=http://localhost:11434

OLLAMA_MODEL=qwen3:8b


# Optional Cloud LLM

GROQ_API_KEY=your_groq_api_key


# LangSmith Monitoring (Optional)

LANGCHAIN_TRACING_V2=true

LANGCHAIN_API_KEY=your_langsmith_api_key

LANGCHAIN_PROJECT=insightforge-ai
```

⚠️ Never upload `.env` files or API keys to GitHub.

---

# 🤖 Ollama Setup

Install Ollama and download the model:

```bash
ollama pull qwen3:8b
```

Start Ollama:

```bash
ollama serve
```

---

# ▶️ Run Application

## Start Backend

```bash
cd backend

uvicorn app.main:app --reload
```

Backend:

```
http://localhost:8000
```

Swagger Documentation:

```
http://localhost:8000/docs
```

---

## Start Frontend

```bash
cd frontend-react

npm install

npm run dev
```

Frontend:

```
http://localhost:5173
```

---

# 🗺️ Roadmap

## V1.0 Beta ✅

Current release includes:

- AI data analysis chatbot
- Dataset intelligence
- Visualization generation
- ML prediction modules
- Automated PDF reports
- React dashboard
- Local LLM support using Ollama


## Future Improvements

- Multi-agent AI workflows
- Real-time dashboards
- Database connectors
- Team collaboration
- Cloud deployment
- Enterprise features


---

# 👨‍💻 Author

## Abdul Samad

AI/ML Engineer focused on:

- Generative AI
- Large Language Models
- Agentic AI
- Machine Learning
- AI-powered applications


GitHub:

https://github.com/AbdulSamad502


LinkedIn:

https://linkedin.com/in/abdul-samad-ai


---

# 📌 Release Note

## InsightForge-AI v1.0 Beta

This is the first beta release of InsightForge-AI.

The current version demonstrates a complete AI-powered business intelligence workflow including:

- Data analysis
- Natural language interaction
- AI agents
- Machine learning insights
- Visualization generation
- Automated reporting


As a **v1.0 Beta version**, the platform will continue to receive improvements, optimizations, and additional enterprise-level capabilities in future releases.

---

<div align="center">

Built with ❤️ using  
**FastAPI · React · LangChain · LangGraph *

</div>
