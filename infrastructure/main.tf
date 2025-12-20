provider "aws" {
  region = var.aws_region
}

# --- NETWORK ---
resource "aws_vpc" "zeus_vpc" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "main" {
  vpc_id     = aws_vpc.zeus_vpc.id
  cidr_block = "10.0.1.0/24"
}

# --- IAM ROLES ---
resource "aws_iam_role" "zeus_role" {
  name = "zeus_eks_cluster_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "eks.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role" "iam_for_lambda" {
  name = "zeus_lambda_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# --- RESOURCES ---
resource "aws_eks_cluster" "zeus_cluster" {
  name     = var.cluster_name
  role_arn = aws_iam_role.zeus_role.arn
  vpc_config {
    subnet_ids = [aws_subnet.main.id]
  }
}

resource "aws_lambda_function" "zeus_monitor" {
  filename      = "lambda_function_payload.zip" 
  function_name = var.lambda_name
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "app.lambda_handler"
  runtime       = "python3.9"
}

resource "aws_instance" "worker_node" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = var.instance_type
  tags = { Name = "Zeus-Worker" }
}
