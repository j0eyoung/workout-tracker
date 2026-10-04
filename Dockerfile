FROM python:3.11-slim

WORKDIR /app

# Install build tools, curl, and Node.js 22 (required by claude-code)
RUN apt-get update && apt-get install -y curl build-essential && \
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g @anthropic-ai/claude-code endurance-coach@latest && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x run.sh

# Streamlit port and FastAPI port
EXPOSE 8501 8000

CMD ["./run.sh"]
