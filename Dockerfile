FROM python:3.11-slim

WORKDIR /app

# Install Node.js and npm to get the Claude Code CLI and the Endurance Coach CLI
RUN apt-get update && apt-get install -y nodejs npm && \
    npm install -g @anthropic-ai/claude-code endurance-coach@latest && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x run.sh

# Streamlit port and FastAPI port
EXPOSE 8501 8000

CMD ["./run.sh"]
