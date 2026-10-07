# Debian 12 (bookworm) ships Python 3.11, which has prebuilt wheels for every pinned
# package. The default node:22-slim is Debian 13 with Python 3.13, where pydantic-core
# and numpy have no wheels and must compile from source (that is what broke 0.1.5).
FROM node:22-bookworm-slim

WORKDIR /app

COPY requirements.txt .

# One layer so the compilers can be removed once the native modules are built
RUN apt-get update \
    && apt-get install -y --no-install-recommends python3 python3-venv build-essential \
    && npm install -g @anthropic-ai/claude-code endurance-coach@latest \
    && python3 -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt \
    && apt-get purge -y build-essential \
    && apt-get autoremove -y \
    && npm cache clean --force \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/opt/venv/bin:$PATH"

COPY . .

RUN chmod +x run.sh

# Streamlit port and FastAPI port
EXPOSE 8501 8000

CMD ["./run.sh"]
