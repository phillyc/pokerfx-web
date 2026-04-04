FROM python:3.11-slim

# Install ffmpeg (for frame extraction) and curl (for health checks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy card detection logic
COPY card_detect_worker.py .
COPY worker.py .

ENV PYTHONUNBUFFERED=1

# The container entrypoint is called by the AWS Batch job definition command.
# Default: run the worker entrypoint.
ENTRYPOINT ["python", "-u", "worker.py"]
