FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y wget unzip && \
    rm -rf /var/lib/apt/lists/*

# Copy necessary files
COPY script.py /app/script.py
COPY config.ini /app/config.ini
COPY bin/innoextract /app/bin/innoextract

# Set permissions for innoextract
RUN chmod +x /app/bin/innoextract

# Set environment variables
ENV WATCH_DIR=/WATCHED
ENV DEST_DIR=/DEST
ENV PROCESSED_DIR=processed

# Create required directories
RUN mkdir -p "$WATCH_DIR" "$DEST_DIR" "$WATCH_DIR/$PROCESSED_DIR"

# Set entrypoint
CMD ["python", "/app/script.py"]
