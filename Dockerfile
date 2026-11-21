FROM python:3.15-slim

# Install ffmpeg with AV1/HEVC support, uv, + deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    wget \
    curl \
    aria2 \
    && curl -LsSf https://astral.sh/uv/install.sh | sh \
    && rm -rf /var/lib/apt/lists/*

ENV PATH="/root/.local/bin:${PATH}"

WORKDIR /app

COPY requirements.txt .
# TgCrypto has no prebuilt wheel for newer Pythons, so compile it, then drop the compiler
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && uv pip install --system --no-cache -r requirements.txt \
    && apt-get purge -y build-essential && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

COPY . .

RUN mkdir -p /tmp/encbot/downloads /tmp/encbot/encodes /tmp/encbot/thumbs

CMD ["python", "-m", "bot"]
