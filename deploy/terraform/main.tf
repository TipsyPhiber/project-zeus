terraform {
  required_version = ">= 1.5"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 6.0"
    }
    kubernetes = {
      source  = "hashicorp/kubernetes"
      version = "~> 2.30"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Required APIs. disable_on_destroy = false avoids tearing down APIs that
# might still be needed by other resources in the project.
resource "google_project_service" "container" {
  service            = "container.googleapis.com"
  disable_on_destroy = false
}

resource "google_project_service" "compute" {
  service            = "compute.googleapis.com"
  disable_on_destroy = false
}

# GKE Autopilot: Google manages nodes, autoscaling, security defaults.
# Cheaper to run than Standard for small workloads.
resource "google_container_cluster" "primary" {
  name             = var.cluster_name
  location         = var.region
  enable_autopilot = true
  deletion_protection = false

  # Required for Autopilot — even an empty block enables VPC-native.
  ip_allocation_policy {}

  depends_on = [
    google_project_service.container,
    google_project_service.compute,
  ]
}

# --- Kubernetes provider, fed by the cluster we just created. ---

data "google_client_config" "default" {}

provider "kubernetes" {
  host                   = "https://${google_container_cluster.primary.endpoint}"
  token                  = data.google_client_config.default.access_token
  cluster_ca_certificate = base64decode(google_container_cluster.primary.master_auth[0].cluster_ca_certificate)
}

# --- App manifests, applied after the cluster exists. ---

resource "kubernetes_namespace" "zeus" {
  count = var.deploy_app ? 1 : 0
  metadata {
    name = "zeus"
  }
}

resource "kubernetes_service_account" "zeus" {
  count = var.deploy_app ? 1 : 0
  metadata {
    name      = "zeus"
    namespace = kubernetes_namespace.zeus[0].metadata[0].name
  }
}

resource "kubernetes_cluster_role" "zeus_reader" {
  count = var.deploy_app ? 1 : 0
  metadata {
    name = "zeus-reader"
  }
  rule {
    api_groups = [""]
    resources  = ["nodes", "pods", "namespaces"]
    verbs      = ["get", "list", "watch"]
  }
}

resource "kubernetes_cluster_role_binding" "zeus_reader" {
  count = var.deploy_app ? 1 : 0
  metadata {
    name = "zeus-reader"
  }
  role_ref {
    api_group = "rbac.authorization.k8s.io"
    kind      = "ClusterRole"
    name      = kubernetes_cluster_role.zeus_reader[0].metadata[0].name
  }
  subject {
    kind      = "ServiceAccount"
    name      = kubernetes_service_account.zeus[0].metadata[0].name
    namespace = kubernetes_namespace.zeus[0].metadata[0].name
  }
}

resource "kubernetes_deployment" "zeus" {
  count = var.deploy_app ? 1 : 0
  metadata {
    name      = "zeus-monitor"
    namespace = kubernetes_namespace.zeus[0].metadata[0].name
    labels    = { app = "zeus-monitor" }
  }
  spec {
    replicas = 1
    selector {
      match_labels = { app = "zeus-monitor" }
    }
    template {
      metadata {
        labels = { app = "zeus-monitor" }
      }
      spec {
        service_account_name = kubernetes_service_account.zeus[0].metadata[0].name
        container {
          name  = "zeus"
          image = var.image
          port {
            container_port = 8080
            name           = "http"
          }
          env {
            name  = "PORT"
            value = "8080"
          }
          resources {
            requests = { cpu = "100m", memory = "128Mi" }
            limits   = { cpu = "500m", memory = "256Mi" }
          }
          readiness_probe {
            http_get {
              path = "/health"
              port = 8080
            }
            initial_delay_seconds = 5
            period_seconds        = 10
          }
          liveness_probe {
            http_get {
              path = "/health"
              port = 8080
            }
            initial_delay_seconds = 15
            period_seconds        = 20
          }
        }
      }
    }
  }
}

resource "kubernetes_service" "zeus" {
  count = var.deploy_app ? 1 : 0
  metadata {
    name      = "zeus-monitor"
    namespace = kubernetes_namespace.zeus[0].metadata[0].name
  }
  spec {
    type = "LoadBalancer"
    selector = { app = "zeus-monitor" }
    port {
      name        = "http"
      port        = 80
      target_port = 8080
      protocol    = "TCP"
    }
  }
}
