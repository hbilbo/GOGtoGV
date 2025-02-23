FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget unzip innoextract && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy necessary files
COPY main.py /app/main.py

# Set environment variables
ENV WATCH_DIR=/WATCHED
ENV DEST_DIR=/DEST
ENV PROCESSED_DIR=processed

# Create required directories
RUN mkdir -p "$WATCH_DIR" "$DEST_DIR" "$WATCH_DIR/$PROCESSED_DIR"

# Set entrypoint
CMD ["python", "/app/main.py"]
