# Use an official Python runtime as the parent image
FROM us-central1-docker.pkg.dev/handshake-build/container-base-images/python:3.11-debian AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
RUN mkdir -p /app
WORKDIR /app

# Install Python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir --upgrade pip \
  && pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

FROM us-central1-docker.pkg.dev/handshake-build/container-base-images/python:3.11-debian AS runner

WORKDIR /app

# Copy compiled wheels from builder stage
COPY --from=builder /app/wheels /app/wheels

# Install Python dependencies
RUN pip install --no-cache /app/wheels/*

# Remove wheels and pip cache
RUN rm -rf /app/wheels \
  && rm -rf /root/.cache/pip/*

# Copy application code and .env
COPY . /app/

RUN adduser -u 1000 app
RUN chown -R 1000 /app
USER 1000

# Expose the port the app runs on
EXPOSE 8080

# Run the script to start the service
WORKDIR /app/
ENTRYPOINT ["python", "main.py"]
