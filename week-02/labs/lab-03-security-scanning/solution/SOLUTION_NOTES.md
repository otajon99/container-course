# Solution Notes: Security Scanning

## The Problem

The starter Dockerfile and dependencies have multiple security issues:

### 1. Outdated Base Image
```dockerfile
FROM python:3.9-slim  # Old version with known CVEs
```

### 2. Outdated Dependencies
```
flask==2.0.1      # Has known vulnerabilities
requests==2.25.1  # Has known vulnerabilities
```

### 3. Running as Root
```dockerfile
# No USER instruction = runs as root
CMD ["python", "app.py"]
```

### 4. No Health Check
Kubernetes and Docker can't detect if the app is actually healthy.

### 5. Poor Layer Ordering
```dockerfile
COPY . .
RUN pip install -r requirements.txt
```
Any file change busts the pip cache.

## The Fixes

### Fix 1: Upgrade Base Image

```dockerfile
FROM python:3.11-slim  # Latest stable Python
```

**Impact:** Fixes OS-level vulnerabilities in:
- libc
- libssl
- System packages
- Python interpreter itself

**How to verify:**
```bash
trivy image --severity CRITICAL,HIGH python:3.9-slim
trivy image --severity CRITICAL,HIGH python:3.11-slim
```

### Fix 2: Update Dependencies

```dockerfile
flask==3.0.0      # Latest stable
requests==2.31.0  # Latest stable
werkzeug==3.0.1   # Latest stable
jinja2==3.1.2     # Latest stable
```

**Impact:** Fixes application-level vulnerabilities.

**How to verify:**
```bash
pip install flask==2.0.1
pip show flask  # Check for known vulnerabilities
pip install flask==3.0.0
```

### Fix 3: Run as Non-Root

```dockerfile
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser
```

**Why this matters:**
- If container is compromised, attacker doesn't have root
- Follows principle of least privilege
- Required by many security policies (PCI-DSS, SOC2)

**Testing:**
```bash
docker exec <container> whoami
# Should output: appuser (not root)
```

### Fix 4: Add Health Check

```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/health', timeout=2)"
```

**Why this matters:**
- Docker can detect unhealthy containers
- Kubernetes can restart failing pods
- Load balancers can remove unhealthy instances

### Fix 5: Optimize Layer Caching

```dockerfile
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY app.py .
```

**Why this matters:**
- Faster rebuilds
- Less time exposed to vulnerabilities during development
- Better CI/CD performance

## Trivy Scan Results

### Before Fixes

```bash
$ trivy image vulnerable-app:v1

vulnerable-app:v1 (debian 11.6)
================================
Total: 87 (CRITICAL: 12, HIGH: 34, MEDIUM: 28, LOW: 13)

CRITICAL: 12
- libssl1.1: CVE-2023-XXXXX
- libc6: CVE-2023-YYYYY
- ... (10 more)

HIGH: 34
- python3.9: CVE-2023-ZZZZZ
- ... (33 more)
```

### After Fixes

```bash
$ trivy image vulnerable-app:v3

vulnerable-app:v3 (debian 12.2)
================================
Total: 3 (CRITICAL: 0, HIGH: 0, MEDIUM: 2, LOW: 1)
```

**Result:** CRITICAL and HIGH vulnerabilities eliminated!

## Understanding the Remaining Vulnerabilities

Even after fixes, you might see MEDIUM or LOW vulnerabilities:

```
MEDIUM: libexpat1: CVE-2023-12345
```

**Questions to ask:**
1. Does my app use libexpat? (Check with `ldd /usr/local/bin/python`)
2. Is the vulnerable code path reachable?
3. Is there a compensating control?

**When to ignore:**
- Vulnerability requires local access (your container is networked)
- Vulnerability affects a feature you don't use
- No fix available yet, and risk is acceptable

**Document it:**
```
# .trivyignore
# libexpat vulnerability - app doesn't parse XML, not exploitable
CVE-2023-12345
```

## Severity Priority Guide

| Severity | Example | Fix Timeline |
|----------|---------|--------------|
| CRITICAL | Remote code execution, no auth required | Immediate (hours) |
| HIGH | Code execution requiring user interaction | Before next deploy (days) |
| MEDIUM | Information disclosure, DoS | Next sprint (weeks) |
| LOW | Theoretical exploits, require complex setup | When convenient (months) |

## Continuous Scanning Strategy

### 1. Scan in Development

```bash
# Before every commit
docker build -t myapp:dev .
trivy image --severity CRITICAL,HIGH --exit-code 1 myapp:dev
```

### 2. Scan in CI/CD

```yaml
# .github/workflows/security.yml
- name: Scan for vulnerabilities
  run: |
    trivy image --severity CRITICAL,HIGH --exit-code 1 $IMAGE_NAME
```

Fails the build if vulnerabilities found.

### 3. Scan in Production (Registry)

```bash
# Scan images already pushed
trivy image ghcr.io/myorg/myapp:v1.2.3
```

### 4. Scheduled Scans

```bash
# Daily cron job
0 2 * * * trivy image --severity CRITICAL,HIGH myapp:latest | mail -s "Security Scan" ops@company.com
```

New CVEs are published daily - images that were clean yesterday might be vulnerable today.

## Common Student Questions

**Q: I upgraded everything but still have MEDIUM vulnerabilities. Is that okay?**
A: Yes! MEDIUM vulnerabilities are acceptable in most cases. Focus on eliminating CRITICAL and HIGH.

**Q: The scan says "no fix available" - what do I do?**
A: 
1. Check if it actually affects your app
2. Add compensating controls (network policies, WAF)
3. Document the risk in .trivyignore
4. Monitor for updates

**Q: Should I scan base images or just my application?**
A: Both! Base images contribute most vulnerabilities (OS packages), but your dependencies matter too.

**Q: How often should I rebuild images to get security updates?**
A: At minimum:
- Weekly for production images
- Daily for development images
- Immediately when CRITICAL CVE affects your stack

**Q: Trivy found vulnerabilities in my Go binary. I thought static binaries were safe?**
A: Go binaries include the Go runtime, which can have vulnerabilities. Also, any dependencies you import. Always scan, even for "static" languages.

## Advanced: Multi-Stage with Security

Combine multi-stage builds with security scanning:

```dockerfile
# Stage 1: Build with latest tools
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: Minimal runtime
FROM python:3.11-slim
WORKDIR /app

# Copy only installed packages
COPY --from=builder /root/.local /root/.local
COPY app.py .

# Non-root user
RUN useradd -m -u 1000 appuser
USER appuser

# Health check
HEALTHCHECK CMD python -c "import requests; requests.get('http://localhost:5000/health')"

ENV PATH=/root/.local/bin:$PATH
CMD ["python", "app.py"]
```

**Benefits:**
- No pip/setuptools in final image (smaller attack surface)
- Still all security best practices applied
- Smaller image = less to scan

## Real-World Integration

### Example: Enforce Security in CI/CD

```yaml
# .github/workflows/build-and-scan.yml
name: Build and Security Scan

on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build image
        run: docker build -t ${{ github.repository }}:${{ github.sha }} .
      
      - name: Run Trivy scan
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: ${{ github.repository }}:${{ github.sha }}
          format: 'sarif'
          output: 'trivy-results.sarif'
          severity: 'CRITICAL,HIGH'
          exit-code: '1'  # Fail if vulnerabilities found
      
      - name: Upload results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        if: always()
        with:
          sarif_file: 'trivy-results.sarif'
      
      - name: Push if scan passes
        if: success()
        run: docker push ${{ github.repository }}:${{ github.sha }}
```

This:
1. Builds the image
2. Scans for CRITICAL and HIGH
3. **Fails the build** if vulnerabilities found
4. Uploads results to GitHub Security tab
5. Only pushes if scan passes

## Key Takeaways

1. **Scan early and often** - Shift security left
2. **Fix CRITICAL and HIGH first** - Prioritize by severity
3. **Automate scanning** - Make it part of CI/CD
4. **Keep images fresh** - Rebuild regularly for security updates
5. **Defense in depth** - Scanning is one layer of many
6. **Document exceptions** - Use .trivyignore with comments explaining why

## Further Reading

- [OWASP Container Security](https://owasp.org/www-community/vulnerabilities/)
- [CIS Docker Benchmark](https://www.cisecurity.org/benchmark/docker)
- [NIST Container Security Guide](https://nvlpubs.nist.gov/nistpubs/SpecialPublications/NIST.SP.800-190.pdf)
