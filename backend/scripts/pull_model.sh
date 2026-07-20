#!/bin/bash
# Automatically pull Ollama model on first run
MODEL=${OLLAMA_MAIN_MODEL:-llama3.2}
echo "Checking if $MODEL is available..."

# Wait for Ollama to be ready
until curl -s http://ollama:11434/api/tags > /dev/null 2>&1; do
    echo "Waiting for Ollama..."
    sleep 2
done

# Check if model exists
if curl -s http://ollama:11434/api/tags | grep -q "$MODEL"; then
    echo "✅ $MODEL already available"
else
    echo "🔽 Downloading $MODEL (first-time setup, may take several minutes)..."
    curl -X POST http://ollama:11434/api/pull -d "{\"name\": \"$MODEL\"}"
    echo "✅ $MODEL downloaded"
fi