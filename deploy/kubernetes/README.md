# Kubernetes manifests

Apply against a cluster you control:

```bash
kubectl apply -f deploy/kubernetes/
```

This creates a `zeus` namespace, a ServiceAccount with read-only RBAC for nodes/pods/namespaces, a Deployment running the app, and a LoadBalancer Service exposing it on port 80.

## Image

The Deployment references `zeus-monitor:latest`. Build and push it to a registry your cluster can pull from, then update `image:` in `deployment.yaml`. Examples:

```bash
# Google Artifact Registry
docker build -t us-central1-docker.pkg.dev/MY_PROJECT/zeus/zeus-monitor:1 .
docker push us-central1-docker.pkg.dev/MY_PROJECT/zeus/zeus-monitor:1

# Docker Hub
docker build -t MY_USER/zeus-monitor:1 .
docker push MY_USER/zeus-monitor:1
```

## What you'll see

Once running, the dashboard's Kubernetes panel will report the cluster version, node readiness, pod counts by phase, and namespace count — read via the in-cluster ServiceAccount. The Docker panel will say "not available" because the pod has no access to the host Docker socket (intentional — mounting it would be a privilege escalation).

The AWS and GCP panels will say "not connected" unless you supply credentials via env vars / mounted Secrets.
