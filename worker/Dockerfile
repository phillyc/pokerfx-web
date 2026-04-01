FROM python:3.11-slim

# Install ffmpeg (for frame extraction)
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy card_detect logic
COPY card_detect.py .
COPY schemas.py .
COPY storage.py .

ENV PYTHONUNBUFFERED=1

# The container entrypoint is handled by the job definition command.
# This Dockerfile is referenced by aws-batch/ job definition.
ENTRYPOINT ["python", "-u", "worker.py"]
