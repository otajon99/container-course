# Lab 3: GitOps Submission — Ship to Production

**Time:** 25 minutes  
**Objective:** Push your updated app to GHCR, write Kubernetes manifests, and submit a pull request that deploys your app to the shared cluster via ArgoCD

---

## How This Works

For the rest of this course, this is the workflow. Every week you'll add features to your app and deploy them through this pipeline:

```
  You (local)                    GitHub                     Shared Cluster
  ──────────                    ──────                     ──────────────
                                                           
  1. Build image ──────────►  2. Push to GHCR
                                     │
  3. Write manifests ─────►  4. Open PR to
                               container-gitops
                                     │
                              5. PR merged ──────────►  6. ArgoCD detects
                                                           change and syncs
                                                              │
                                                        7. Your app is live
                                                           with a public URL
```

No one runs `kubectl apply` on the shared cluster. The Git repo **is** the source of truth. If it's not in the repo, it doesn't exist in production.

---

## Part 1: Push Your Image to GHCR

You did this in Week 1, but now with the v4 tag:

```bash
cd week-04/labs/lab-02-deploy-and-scale/starter

# Make sure you've customized app.py with your name/username

# Tag for GHCR
docker tag student-app:v4 ghcr.io/<YOUR_GITHUB_USERNAME>/container-course-app:v4

# Log in to GHCR (use a Personal Access Token with packages:write scope)
echo $GITHUB_TOKEN | docker login ghcr.io -u <YOUR_GITHUB_USERNAME> --password-stdin

# Push
docker push ghcr.io/<YOUR_GITHUB_USERNAME>/container-course-app:v4
```

> **Note:** We renamed the image from `container-course-student` (Week 1) to `container-course-app`. This is the same app evolving — it'll grow new features each week.

### Make It Public

Your image must be publicly pullable so the shared cluster can access it without credentials:

1. Go to `https://github.com/<YOUR_USERNAME>?tab=packages`
2. Click on `container-course-app`
3. **Package settings** → **Danger zone** → Change visibility to **Public**

---

## Part 2: Create Your Manifests

Clone the gitops repo (or pull latest if you already have it):

```bash
cd ~/
git clone https://github.com/ziyotek-edu/container-gitops.git
cd container-gitops
git checkout -b week04/<YOUR_GITHUB_USERNAME>
```

### Create Your Directory

Each student gets their own directory under `students/`. This is where all your manifests live for the entire course:

```bash
mkdir -p students/<YOUR_GITHUB_USERNAME>
```

### Write deployment.yaml

Create `students/<YOUR_GITHUB_USERNAME>/deployment.yaml`:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: student-<YOUR_GITHUB_USERNAME>
  labels:
    app: student-app
    student: <YOUR_GITHUB_USERNAME>
    week: "4"
spec:
  replicas: 1
  selector:
    matchLabels:
      app: student-app
      student: <YOUR_GITHUB_USERNAME>
  template:
    metadata:
      labels:
        app: student-app
        student: <YOUR_GITHUB_USERNAME>
    spec:
      containers:
      - name: student-app
        image: ghcr.io/<YOUR_GITHUB_USERNAME>/container-course-app:v4
        ports:
        - containerPort: 5000
          name: http
        env:
        - name: STUDENT_NAME
          value: "YOUR_FULL_NAME"
        - name: GITHUB_USERNAME
          value: "<YOUR_GITHUB_USERNAME>"
        - name: APP_VERSION
          value: "v4"
        - name: ENVIRONMENT
          value: "production"
        - name: POD_NAME
          valueFrom:
            fieldRef:
              fieldPath: metadata.name
        - name: POD_NAMESPACE
          valueFrom:
            fieldRef:
              fieldPath: metadata.namespace
        - name: POD_IP
          valueFrom:
            fieldRef:
              fieldPath: status.podIP
        - name: NODE_NAME
          valueFrom:
            fieldRef:
              fieldPath: spec.nodeName
        resources:
          requests:
            memory: "64Mi"
            cpu: "50m"
          limits:
            memory: "256Mi"
            cpu: "200m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
```

**Replace** all instances of `<YOUR_GITHUB_USERNAME>` and `YOUR_FULL_NAME`.

### Write service.yaml

Create `students/<YOUR_GITHUB_USERNAME>/service.yaml`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: student-<YOUR_GITHUB_USERNAME>-svc
  labels:
    app: student-app
    student: <YOUR_GITHUB_USERNAME>
spec:
  selector:
    app: student-app
    student: <YOUR_GITHUB_USERNAME>
  ports:
  - port: 80
    targetPort: 5000
    protocol: TCP
    name: http
```

### Write kustomization.yaml

Create `students/<YOUR_GITHUB_USERNAME>/kustomization.yaml`:

```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization

resources:
  - deployment.yaml
  - service.yaml
```

This file tells Kustomize (and ArgoCD) which manifests to apply. As you add more resources in future weeks (ConfigMaps, Secrets, Ingress), you'll add them to this list.

### Verify Your Directory

Your directory should look like this:

```
students/<YOUR_GITHUB_USERNAME>/
├── deployment.yaml
├── kustomization.yaml
└── service.yaml
```

### Validate Locally

Before pushing, make sure your YAML is valid:

```bash
# Quick syntax check
kubectl apply --dry-run=client -f students/<YOUR_GITHUB_USERNAME>/deployment.yaml
kubectl apply --dry-run=client -f students/<YOUR_GITHUB_USERNAME>/service.yaml

# Kustomize build (shows you what ArgoCD will see)
kubectl kustomize students/<YOUR_GITHUB_USERNAME>/
```

If `kubectl kustomize` produces valid YAML output with both your Deployment and Service, you're good.

---

## Part 3: Submit Your Pull Request

```bash
git add students/<YOUR_GITHUB_USERNAME>/
git commit -m "week04: add manifests for <YOUR_GITHUB_USERNAME>"
git push origin week04/<YOUR_GITHUB_USERNAME>
```

Go to the `container-gitops` repo on GitHub and open a pull request:

- **Base:** `main`
- **Compare:** `week04/<YOUR_GITHUB_USERNAME>`
- **Title:** `Week 04: <YOUR_NAME> - Kubernetes deployment`

The PR validation workflow will run and check that your manifests are syntactically valid. Once a reviewer approves and merges, ArgoCD picks up the change.

---

## Part 4: Watch the Deployment

After your PR is merged, ArgoCD will detect the new manifests and sync them to the shared cluster. This usually takes 1-3 minutes.

### Check ArgoCD (If Dashboard Access Is Available)

Your instructor may provide access to the ArgoCD dashboard where you can see your application syncing in real time.

### Verify with kubectl

```bash
# Switch to the shared cluster context
kubectl config use-context shared-cluster

# Check your namespace for the new pod
kubectl get pods -n student-<YOUR_GITHUB_USERNAME>

# See the full deployment
kubectl get all -n student-<YOUR_GITHUB_USERNAME>

# Check the logs
kubectl logs deployment/student-<YOUR_GITHUB_USERNAME> -n student-<YOUR_GITHUB_USERNAME>

# Test the info endpoint via port-forward
kubectl port-forward -n student-<YOUR_GITHUB_USERNAME> service/student-<YOUR_GITHUB_USERNAME>-svc 8080:80 &
curl localhost:8080/info
kill %1
```

### Check the Public URL

If DNS is configured, your app should be accessible at:

```
https://<YOUR_GITHUB_USERNAME>.students.yourdomain.com
```

Your instructor will confirm the URL pattern.

---

## Part 5: Switch Back to Local

Always switch back to your local cluster when you're done checking the shared one:

```bash
kubectl config use-context kind-lab
```

---

## The Pattern Going Forward

This is how every subsequent week works:

1. **Get the code drop** — new features added to `app.py` (Redis support, new endpoints, etc.)
2. **Build and test locally** — `docker build`, load into kind, `kubectl apply`, verify
3. **Push image to GHCR** — `docker push ghcr.io/<username>/container-course-app:<tag>`
4. **Update gitops manifests** — modify files in `students/<username>/`, add new resources
5. **Open PR** — validation runs, reviewer merges
6. **ArgoCD deploys** — your changes go live on the shared cluster

Each week you'll add files to your `students/<username>/` directory. The `kustomization.yaml` grows with each new resource. By Week 8, your directory will contain Deployments, Services, ConfigMaps, Secrets, Ingress rules, and more — a complete application stack managed entirely through Git.

---

## Checkpoint ✅

Before you're done, verify:

- [ ] Your v4 image is on GHCR and publicly accessible
- [ ] Your `students/<username>/` directory has deployment.yaml, service.yaml, and kustomization.yaml
- [ ] `kubectl kustomize students/<username>/` produces valid output
- [ ] Your PR is submitted (or merged)
- [ ] After merge: your pod is running on the shared cluster
- [ ] After merge: the `/info` endpoint returns real pod metadata on the shared cluster
- [ ] You're back on the `kind-lab` context

---

## What You Accomplished Today

Think about what happened in 3 hours:

- You built a local Kubernetes cluster from scratch
- You learned how the control plane components work together
- You deployed an application, scaled it, updated it with zero downtime, and rolled it back
- You debugged failing pods using logs, describe, and exec
- You shipped your app to a production cluster through a Git-driven pipeline

The container you built in Week 1 is now a Kubernetes-managed application with health checks, resource limits, pod metadata injection, and an automated deployment pipeline.

Next week, we wire in Redis.
