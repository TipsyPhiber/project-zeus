variable "project_id" {
  description = "GCP project ID. Required."
  type        = string
}

variable "region" {
  description = "GCP region for the GKE Autopilot cluster."
  type        = string
  default     = "us-central1"
}

variable "cluster_name" {
  description = "Name of the GKE cluster."
  type        = string
  default     = "zeus-cluster"
}

variable "image" {
  description = "Container image for the Zeus dashboard. Must be pullable from the cluster."
  type        = string
  default     = "zeus-monitor:latest"
}

variable "deploy_app" {
  description = "If true, also deploy the Zeus app manifests via the kubernetes provider after the cluster comes up."
  type        = bool
  default     = true
}
