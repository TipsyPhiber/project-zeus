variable "aws_region" {
  description = "The AWS region to deploy resources into"
  default     = "us-west-2"
}

variable "cluster_name" {
  description = "The name of the Kubernetes (EKS) cluster"
  default     = "zeus-prod-cluster"
}

variable "lambda_name" {
  description = "The function name for the serverless monitor"
  default     = "zeus_resource_monitor"
}

variable "instance_type" {
  description = "The size of the worker nodes"
  default     = "t2.micro"
}
