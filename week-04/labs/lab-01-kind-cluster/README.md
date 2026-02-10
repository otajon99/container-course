# Lab 1: Create Your kind Cluster & Explore

**Time:** 30 minutes  
**Objective:** Stand up a local Kubernetes cluster, learn essential kubectl commands, and discover that your Week 1 apps are already running on Kubernetes

---

## Part 1: Create Your Local Cluster

kind (Kubernetes IN Docker) runs Kubernetes nodes as Docker containers. You already have Docker, so this is the fastest way to get a real cluster on your machine.

### Create the Cluster

```bash
kind create cluster --name lab
```

This takes about 60 seconds. kind is pulling a node image (a Docker container that runs `kubelet`, `kube-proxy`, and the control plane components), then bootstrapping a single-node Kubernetes cluster inside it.

When it finishes, you'll see:

```
Creating cluster "lab" ...
 ✓ Ensuring node image (kindest/node:v1.32.2) 🖼
 ✓ Preparing nodes 📦
 ✓ Writing configuration 📜
 ✓ Starting control-plane 🕹️
 ✓ Installing CNI 🔌
 ✓ Installing StorageClass 💾
Set kubectl context to "kind-lab"
```

### Verify

```bash
kubectl cluster-info --context kind-lab
```

You should see the API server address (something like `https://127.0.0.1:PORT`).

### What Just Happened?

Let's peek behind the curtain. Your "cluster" is a Docker container:

```bash
docker ps
```

You'll see a container named `lab-control-plane` running the `kindest/node` image. That single container is running the entire Kubernetes control plane plus acting as a worker node. For learning purposes, this is all we need.

```bash
# See the Kubernetes components running inside the "node"
kubectl get pods -n kube-system
```

These are the components from the lecture: `etcd`, `kube-apiserver`, `kube-controller-manager`, `kube-scheduler`, `coredns`, and the CNI (network plugin). They're running as pods inside the cluster — Kubernetes uses itself to run its own components.

---

## Part 2: kubectl — Your Primary Tool

`kubectl` is how you interact with any Kubernetes cluster. Every command follows the pattern:

```
kubectl <verb> <resource> [name] [flags]
```

### Essential Commands

**Explore what's in the cluster:**

```bash
# List all nodes (just one for kind)
kubectl get nodes

# Detailed node info — CPU, memory, OS, container runtime
kubectl describe node lab-control-plane

# List all namespaces
kubectl get namespaces
```

**Namespaces** are virtual partitions within a cluster. Think of them like folders that keep resources organized and isolated. Your kind cluster came with:
- `default` — where your resources go if you don't specify a namespace
- `kube-system` — Kubernetes internal components
- `kube-public` — readable by everyone, rarely used
- `local-path-storage` — kind's storage provider

**Get resources in a specific namespace:**

```bash
# What's running in kube-system?
kubectl get pods -n kube-system

# Get ALL resources across ALL namespaces
kubectl get all --all-namespaces
```

**Get more detail:**

```bash
# Wide output shows node placement and IPs
kubectl get pods -n kube-system -o wide

# Full YAML representation of any resource
kubectl get pod -n kube-system etcd-lab-control-plane -o yaml
```

### The API Resources

Kubernetes has dozens of resource types. See them all:

```bash
kubectl api-resources
```

For now, the ones that matter are:

| Resource | Short Name | What It Does |
|----------|-----------|-------------|
| pods | po | Smallest runnable unit |
| deployments | deploy | Manages replica sets of pods |
| services | svc | Stable network endpoints |
| replicasets | rs | Ensures N pod copies exist |
| namespaces | ns | Virtual cluster partitions |
| configmaps | cm | Configuration data |
| secrets | — | Sensitive configuration data |
| events | ev | Log of what happened in the cluster |

### Practice: Explore the Cluster

Before moving on, try these commands and observe the output:

```bash
# How many CPU cores and how much memory does your node have?
kubectl describe node lab-control-plane | grep -A 5 "Capacity:"

# What container runtime is this node using?
kubectl describe node lab-control-plane | grep "Container Runtime"

# What pods are using the most resources?
kubectl top pods -n kube-system 2>/dev/null || echo "Metrics server not installed (expected for kind)"

# List all events in the cluster — this is your first debugging tool
kubectl get events --all-namespaces --sort-by=.metadata.creationTimestamp
```

---

## Part 3: Pull Back the Curtain

Remember Week 1? You built a container image, pushed it to GHCR, and submitted a pull request to the `container-gitops` repo. You were told your app was "deployed." But deployed where?

It's time to find out.

### Connect to the Shared Cluster

Your instructor will provide connection details. Set up the context:

```bash
# Your instructor will provide this command or file
export KUBECONFIG=~/.kube/shared-config
```

Or if your instructor gave you a direct command:

```bash
# Example — your instructor will provide the actual command
kubectl --kubeconfig ~/.kube/shared-config get nodes
```

### See Your Apps

```bash
# Switch context to the shared cluster
kubectl config use-context shared-cluster  # name may vary

# List the namespaces — look for container-course-week01
kubectl get namespaces | grep container

# There it is. Let's see what's running:
kubectl get pods -n container-course-week01
```

You should see pods with names like `student-almsid-*`, `student-otajon99-*`, `student-emmzi55-*`. Those are the Week 1 containers — your containers — running on a real Kubernetes cluster.

```bash
# See the full picture: deployments, services, pods
kubectl get all -n container-course-week01

# Look at one deployment in detail
kubectl describe deployment student-<YOUR_USERNAME> -n container-course-week01

# Check the logs of your running app
kubectl logs deployment/student-<YOUR_USERNAME> -n container-course-week01
```

### What's Actually Running?

```bash
# See the exact container image each pod is running
kubectl get pods -n container-course-week01 -o jsonpath='{range .items[*]}{.metadata.name}{"\t"}{.spec.containers[0].image}{"\n"}{end}'
```

Those are the GHCR images you pushed in Week 1. The PR you submitted added an entry to `students/week-01.yaml`. A GitHub Actions workflow generated Kubernetes manifests (Deployment + Service) for each student. ArgoCD watched the repo and deployed those manifests to this cluster.

You've been running on Kubernetes since Week 1. You just didn't know it yet.

### Switch Back to Local

For the rest of today's labs, we work on your local kind cluster:

```bash
kubectl config use-context kind-lab
```

> **Tip:** You can always check which cluster you're talking to:
> ```bash
> kubectl config current-context
> ```
> This becomes critical when you have two clusters. Accidentally running `kubectl delete` on the wrong context is a real-world mistake that ruins someone's day.

---

## Part 4: Run a Quick Pod (Optional Exploration)

Before we get into Deployments in Lab 2, let's see what a raw pod looks like:

```bash
# Run a single nginx pod
kubectl run test-nginx --image=nginx --port=80

# Watch it come up
kubectl get pods -w
```

Press `Ctrl+C` once the pod shows `Running`.

```bash
# Describe it — see all the events that led to it running
kubectl describe pod test-nginx

# Read the events from the bottom up:
# 1. Scheduled — scheduler picked a node
# 2. Pulling — kubelet pulling the image
# 3. Pulled — image download complete
# 4. Created — container created
# 5. Started — container running
```

Now delete it:

```bash
kubectl delete pod test-nginx
```

It's gone. Permanently. There's no controller watching this pod because we created it directly, not through a Deployment. This is why you almost never create bare pods — there's nothing to bring them back if they die.

---

## Checkpoint ✅

Before moving on, verify:

- [ ] `kubectl get nodes` shows your kind cluster node as `Ready`
- [ ] You can list pods in `kube-system`
- [ ] You connected to the shared cluster and saw the Week 1 pods
- [ ] You understand which context (local vs shared) you're currently using
- [ ] You're back on the `kind-lab` context for the next lab

---

## Next Lab

Continue to [Lab 2: Deploy, Scale, Update, Debug](../lab-02-deploy-and-scale/)
