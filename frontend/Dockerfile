FROM python:3.11-slim

WORKDIR /app

# Install Streamlit + dependencies
RUN pip install --no-cache-dir \
    streamlit==1.39.0 \
    httpx==0.27.2 \
    plotly==5.24.1 \
    python-dotenv==1.0.1

# Copy frontend code
COPY . .

# Non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--browser.gatherUsageStats=false"]