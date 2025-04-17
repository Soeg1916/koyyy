FROM python:3.9-slim

# Install dependencies for Pillow and other requirements
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Make sure we expose the port the app runs on
EXPOSE 5000

# Command to run the application
CMD ["python", "main.py"]
