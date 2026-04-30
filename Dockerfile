FROM python:3.11-slim

# Install ffmpeg with AV1/HEVC support, uv, + deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    wget \
    curl \
    aria2 \
    libsvtav1-enc0 \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
RUN uv pip install --system --no-cache -r requirements.txt

COPY . .

RUN mkdir -p /tmp/encbot/downloads /tmp/encbot/encodes /tmp/encbot/thumbs

CMD ["python", "-m", "bot"]
