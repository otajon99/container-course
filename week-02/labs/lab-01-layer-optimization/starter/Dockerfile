FROM python:3.11-slim

WORKDIR /app

# ❌ ANTI-PATTERN: Copy everything first
# This invalidates the cache every time ANY file changes
COPY . .

# This expensive operation runs every time app.py changes
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]
