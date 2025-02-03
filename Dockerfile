# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Change mirror
RUN sed -i 's/deb.debian.org/mirrors.aliyun.com/g' /etc/apt/sources.list.d/debian.sources

# Download the curl
RUN apt-get update && apt-get install -y curl --no-install-recommends && rm -rf /var/lib/apt/lists/*

# Install the required dependencies
RUN pip install --no-cache-dir gunicorn gevent -i https://mirrors.aliyun.com/pypi/simple

# Copy the requirements file into the container
COPY requirements.txt .

# Install the dependencies
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple

# Copy the rest of the application code into the container
COPY src/ ./src/

# Set the environment variable for the entry point
ENV PYTHONPATH=/app/src

# Command to run the application
CMD ["python", "-m", "gunicorn", "-c", "src/gunicorn_config.py", "src.server:app"]

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/git/ping || exit 1

# Expose the port the application runs on
EXPOSE 8000