# Use a minimal Python 3.11 image as the base
FROM python:3.11-slim

# Prevent Python from writing .pyc files and force unbuffered output for logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for:
# - mysqlclient (MySQL development headers and compiler)
# - wait-for-it.sh (curl and dos2unix)
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    curl \
    dos2unix \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependency definitions and install them without caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend application code into the container image
COPY . .

# Convert wait-for-it.sh line endings to UNIX format and ensure it’s executable
RUN dos2unix ./scripts/wait-for-it.sh && \
    chmod +x ./scripts/wait-for-it.sh

# Inform Docker this container will use port 8000
EXPOSE 8000

# Default command to run the Django development server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
