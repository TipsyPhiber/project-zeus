output "cluster_name" {
  value = google_container_cluster.primary.name
}

output "cluster_location" {
  value = google_container_cluster.primary.location
}

output "kubectl_credentials" {
  description = "Run this to point kubectl at the new cluster."
  value       = "gcloud container clusters get-credentials ${google_container_cluster.primary.name} --region ${google_container_cluster.primary.location} --project ${var.project_id}"
}

output "service_load_balancer_ip" {
  description = "Public IP of the LoadBalancer service. May be empty for the first minute or two while GCP provisions it."
  value       = var.deploy_app ? try(kubernetes_service.zeus[0].status[0].load_balancer[0].ingress[0].ip, "(provisioning — check `kubectl get svc -n zeus` in a minute)") : null
}
