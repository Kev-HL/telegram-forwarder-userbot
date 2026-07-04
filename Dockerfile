# Telegram Forwarder Userbot

# Use slim Python image for smaller size
FROM python:3.12.3-slim-bookworm

# Basic ownership labels
LABEL maintainer="Kev-HL (GitHub)"
LABEL org.opencontainers.image.source="https://github.com/Kev-HL/telegram-forwarder-userbot"

# Set setup working directory
WORKDIR /app

# Create a non-root user and group (botuser)
RUN addgroup --system botuser && adduser --system --ingroup botuser botuser

# Set runtime env defaults
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DATA_DIR=/data

# Copy requirements.txt
COPY requirements.txt ./

# Install Python base dependencies
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code and build setup files
COPY pyproject.toml ./
COPY src ./src

# Install local package
RUN pip install --no-cache-dir .

# Copy main and setup bot scripts
COPY main.py init_bot.py ./

# Prepare runtime data dir and ownership
RUN mkdir -p /data && chown -R botuser:botuser /data /app
VOLUME ["/data"]

# Switch to non-root user
USER botuser

# Default command: run bot
CMD ["python", "main.py"]