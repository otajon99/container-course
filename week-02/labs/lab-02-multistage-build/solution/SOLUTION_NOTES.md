# Solution Notes: Multi-Stage Builds

## The Problem

The single-stage Dockerfile includes the entire Go toolchain in the final image:

```dockerfile
FROM golang:1.21    # ~800MB base image
# ... build steps ...
CMD ["./server"]    # Final image includes compiler, build cache, source code
```

**Result:** ~1.0-1.2GB image for a ~10MB binary

## The Solution: Multi-Stage Build

### Stage 1: Builder

```dockerfile
FROM golang:1.21 AS builder
# Build the binary with all necessary tools
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server .
```

Uses the full golang image to compile the application.

### Stage 2: Runtime

```dockerfile
FROM alpine:3.18
COPY --from=builder /app/server .
CMD ["./server"]
```

Only copies the compiled binary to a minimal base image.

## Size Comparison

| Image Type | Base | Size | Contents |
|------------|------|------|----------|
| Single-stage | golang:1.21 | ~1.2GB | Compiler, tools, source, binary |
| Multi-stage (Alpine) | alpine:3.18 | ~15MB | Binary only + minimal OS |
| Multi-stage (Scratch) | scratch | ~10MB | Binary only |

## Build Flags Explained

```bash
CGO_ENABLED=0
```
- Disables CGO (C bindings)
- Creates a static binary with no external dependencies
- Required for `scratch` base image
- Works on Alpine without musl compatibility issues

```bash
GOOS=linux
```
- Targets Linux even if building on macOS/Windows
- Ensures binary works in Linux containers

```bash
-ldflags="-w -s"
```
- `-w` disables DWARF debugging information
- `-s` disables symbol table
- Result: 20-30% smaller binary
- Trade-off: Harder to debug crashes

## Why Alpine vs Scratch?

### Alpine (3.18)
**Pros:**
- Has a shell (`/bin/sh`) for debugging
- Package manager (apk) if you need to add tools
- Can run as non-root user easily
- ~7MB base

**Cons:**
- Slightly larger than scratch
- Uses musl libc (can cause issues with some binaries)

**Use when:** You want a balance of small size and debuggability

### Scratch
**Pros:**
- Literally 0MB base
- Smallest possible image
- Maximum security (no shell to exploit)

**Cons:**
- No shell - can't `docker exec` into it
- No package manager
- Harder to debug issues
- Binary must be fully static

**Use when:** Security and size are paramount, debugging can happen elsewhere

## Common Pitfalls

### 1. CGO_ENABLED=1 with scratch

```dockerfile
# ❌ This will fail
RUN go build -o server .    # CGO enabled by default
FROM scratch
COPY --from=builder /app/server .
```

**Error:** Binary expects glibc, which doesn't exist in scratch.

**Fix:** `CGO_ENABLED=0`

### 2. Forgetting GOOS=linux

Building on macOS creates a Darwin binary, which won't run in Linux containers.

### 3. Not using AS to name the builder stage

```dockerfile
# Works but ugly
COPY --from=0 /app/server .

# Better
FROM golang:1.21 AS builder
COPY --from=builder /app/server .
```

## Teaching Points

1. **Multi-stage !== multi-container:** All stages build in one `docker build`, but only the last stage becomes the image.

2. **COPY --from is the magic:** This is what pulls artifacts from earlier stages.

3. **Different base images per stage:** Builder can use golang:1.21 (1GB), runtime can use alpine (7MB).

4. **Security benefit:** No compiler in production = attackers can't compile malicious code even if they compromise the container.

5. **Real-world impact:** In a 100-pod deployment:
   - Single-stage: 120GB network transfer
   - Multi-stage: 1.5GB network transfer
   - 98.75% reduction!

## Extension Ideas

### For Advanced Students

**Challenge:** Optimize the Python Flask app from Week 1 using multi-stage builds.

**Approach:**
```dockerfile
FROM python:3.11 AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.11-slim
COPY --from=builder /install /usr/local
COPY app.py .
CMD ["python", "app.py"]
```

This is harder because Python can't create static binaries, but you can skip pip in the final image.

## Common Student Questions

**Q: Why is the binary so big (10MB) for such a simple app?**
A: Go includes the entire runtime (garbage collector, goroutine scheduler, etc.) in the binary. It's not like C where you link against shared libraries. This is a trade-off: larger binaries, but easier deployment.

**Q: Can I use multi-stage builds with languages other than Go?**
A: Yes! Node.js, Rust, Java, C/C++ all benefit. Even Python can use it to skip pip/setuptools in the final image.

**Q: What if I need to debug the production container?**
A: Use Alpine for production, not scratch. Or build a separate "debug" image with tools included.

**Q: The alpine image says "musl libc" - what does that mean?**
A: Alpine uses musl instead of glibc (the standard C library). For Go with CGO_ENABLED=0, this doesn't matter. But for binaries expecting glibc, they won't work on Alpine without recompilation.
