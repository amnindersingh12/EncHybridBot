FROM python:3.11-slim

# Install ffmpeg with AV1/HEVC support + deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    wget \
    curl \
    aria2 \
    libsvtav1-enc0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /tmp/encbot/downloads /tmp/encbot/encodes /tmp/encbot/thumbs

CMD ["python", "-m", "bot"]
