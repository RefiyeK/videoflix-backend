# Base image: slim Python for a smaller footprint
FROM python:3.12-slim

# Keep Python output unbuffered and skip .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Working directory inside the container
WORKDIR /app

# Install FFMPEG for HLS video conversion (needed by the RQ worker)
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first (better layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Make the entrypoint executable
RUN chmod +x /app/entrypoint.sh

# Django's default port
EXPOSE 8000

# Run migrations then the container command
ENTRYPOINT ["/app/entrypoint.sh"]