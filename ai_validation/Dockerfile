# Use a base image with OpenCV dependencies already installed
FROM python:3.11-slim

# Install system packages
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Default port for Render
EXPOSE 10000

# Start command with uvicorn (using PORT environment variable)
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "10000"]