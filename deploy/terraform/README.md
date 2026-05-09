# Terraform: GKE Autopilot + Zeus app

Provisions a GKE Autopilot cluster in your GCP project, then deploys the Zeus dashboard to it. One `terraform apply` does both.

## Prerequisites

1. **GCP project with billing enabled.** Autopilot is cheap (a few cents/hour idle) but not free.
2. **`gcloud` CLI** authenticated: `gcloud auth application-default login`.
3. **Terraform CLI** (1.5+): <https://developer.hashicorp.com/terraform/install>.
4. **A pushed image.** Build and push `zeus-monitor` to a registry the cluster can pull from:
   ```bash
   # Example: Google Artifact Registry in your project
   gcloud artifacts repositories create zeus --repository-format=docker --location=us-central1
   gcloud auth configure-docker us-central1-docker.pkg.dev
   docker build -t us-central1-docker.pkg.dev/MY_PROJECT/zeus/zeus-monitor:1 ../..
   docker push us-central1-docker.pkg.dev/MY_PROJECT/zeus/zeus-monitor:1
   ```

## Apply

```bash
cd deploy/terraform
terraform init
terraform apply \
  -var="project_id=MY_PROJECT" \
  -var="image=us-central1-docker.pkg.dev/MY_PROJECT/zeus/zeus-monitor:1"
```

First apply takes ~5–8 minutes (GKE Autopilot provisioning + Load Balancer).

## Get the URL

```bash
terraform output service_load_balancer_ip
# or
gcloud container clusters get-credentials zeus-cluster --region us-central1 --project MY_PROJECT
kubectl get svc -n zeus zeus-monitor
```

Open `http://<EXTERNAL-IP>` in your browser.

## Tear down

```bash
terraform destroy -var="project_id=MY_PROJECT"
```

This removes the cluster, the LoadBalancer, and the deployment. The enabled APIs are left enabled (`disable_on_destroy = false`) so you don't break other resources in the project.

## Notes

- `deletion_protection = false` is set on the cluster so `terraform destroy` works without manual intervention. For a real production cluster you'd flip this to `true`.
- The kubernetes provider authenticates using the gcloud-provided token. That token lasts ~1 hour; if a long apply runs over that, re-run `terraform apply` to refresh.
- This Terraform has not been deployed from this environment — it should plan cleanly, but you'll want to review the plan before applying to your account.
