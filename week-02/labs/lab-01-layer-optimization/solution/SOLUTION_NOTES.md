# Solution Notes: Layer Optimization

## The Problem

The starter Dockerfile uses this order:

```dockerfile
COPY . .                              # Copies everything
RUN pip install -r requirements.txt   # Installs packages
```

**Issue:** Any file change (including `app.py`) invalidates the `COPY . .` layer, which forces Docker to rebuild the `pip install` layer.

## The Fix

Reorder to copy dependencies first:

```dockerfile
COPY requirements.txt .               # Only copy what pip needs
RUN pip install -r requirements.txt   # Cached unless requirements.txt changes
COPY . .                              # Code changes don't bust pip cache
```

## Why It Works

Docker layer caching rules:
1. If an instruction changes, that layer and ALL subsequent layers rebuild
2. For COPY, Docker checks file contents (checksums)
3. Changing `app.py` doesn't change `requirements.txt`, so the pip layer stays cached

## Performance Impact

| Scenario | Bad Dockerfile | Optimized Dockerfile |
|----------|---------------|---------------------|
| First build (cold cache) | ~3 minutes | ~3 minutes |
| Rebuild after changing app.py | ~3 minutes | ~5 seconds |
| Rebuild after changing requirements.txt | ~3 minutes | ~3 minutes |

## Advanced Optimization

For even better caching, separate files by change frequency:

```dockerfile
COPY requirements.txt .      # Changes rarely
RUN pip install -r requirements.txt
COPY data/ ./data/           # Changes occasionally  
COPY app.py .                # Changes frequently
```

Now changing `app.py` only rebuilds the final layer.

## Key Principle

> Order Dockerfile instructions from **least frequently changing** to **most frequently changing**.

This maximizes cache hits and minimizes rebuild time.
