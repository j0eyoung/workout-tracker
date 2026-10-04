FROM node:22-slim

WORKDIR /app

# Install python3 and build tools in the Node 22 image
RUN apt-get update && apt-get install -y python3 python3-pip python3-venv build-essential && \
    npm install -g @anthropic-ai/claude-code endurance-coach@latest && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Create a Python virtual environment (Debian 12 requires venv for pip installs)
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN chmod +x run.sh

# Streamlit port and FastAPI port
EXPOSE 8501 8000

CMD ["./run.sh"]
