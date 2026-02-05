# VULNERABLE DOCKERFILE FOR SECURITY SCANNING LAB
# This Dockerfile intentionally violates security best practices

# Using an older Python version with known vulnerabilities
FROM python:3.9-slim

WORKDIR /app

# Copy everything at once (not optimal for caching)
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose the port
EXPOSE 5000

# Running as root (security risk!)
# No USER instruction means container runs as root

# No health check defined
# No resource limits

CMD ["python", "app.py"]
