# Dockerfile for Harmonic Precision Analyzer API
# Modulo 1 - Análisis Armónico de Cannibal Child
# Use Python 3.11 slim image as base
FROM python:3.11-slim
# Set working directory
WORKDIR /app
# Install system dependencies for music21 and other requirements
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*
# Copy requirements first for better caching
COPY requirements.txt .
# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
# Copy application files
COPY harmonic_precision_analyzer.py .
COPY app.py .
COPY docs ./docs
# Create directory for temporary files
RUN mkdir -p /tmp/uploads
# Expose port 5000
EXPOSE 5000
# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PORT=5000
# Health check
