provider "aws" {
  region = var.aws_region
}

# --- AUTOMATIC ZIPPING ---
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/lambda_function.py"
  output_path = "${path.module}/lambda_function_payload.zip"
}

# --- NETWORK CONFIGURATION ---
resource "aws_vpc" "zeus_vpc" {
  cidr_block = "10.0.0.0/16"
  tags = {
    Name = "Zeus-VPC"
  }
}

resource "aws_subnet" "main" {
  vpc_id     = aws_vpc.zeus_vpc.id
  cidr_block = "10.0.1.0/24"
  tags = {
    Name = "Zeus-Subnet-1"
  }
}

# --- IAM ROLES & SECURITY ---
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

# --- COMPUTE RESOURCES (EKS & EC2) ---
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
  tags = { 
    Name = "Zeus-Worker"
    Type = "Compute"
  }
}

# --- STORAGE & LOGGING ---
resource "aws_s3_bucket" "zeus_logs" {
  bucket = var.s3_bucket_name
  tags = {
    Name        = "Zeus Logs"
    Environment = "Production"
  }
}

# --- CI/CD PIPELINE ---
resource "aws_codepipeline" "zeus_pipeline" {
  name     = "zeus-deployment-pipeline"
  role_arn = aws_iam_role.zeus_role.arn

  artifact_store {
    location = aws_s3_bucket.zeus_logs.bucket
    type     = "S3"
  }

  stage {
    name = "Source"
    action {
      name             = "Source"
      category         = "Source"
      owner            = "AWS"
      provider         = "S3"
      version          = "1"
      output_artifacts = ["source_output"]
      configuration = {
        S3Bucket = aws_s3_bucket.zeus_logs.bucket
        S3Key    = "source.zip"
      }
    }
  }
  
  stage {
    name = "Build"
    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      input_artifacts  = ["source_output"]
      version          = "1"
      configuration = {
        ProjectName = "ZeusBuild"
      }
    }
  }
}

# --- BUILD SERVER (Matches Resume Claim) ---
resource "aws_codebuild_project" "zeus_build" {
  name          = "ZeusBuild"
  description   = "Builds the Zeus Docker container"
  build_timeout = "5"
  service_role  = aws_iam_role.zeus_role.arn

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                       = "aws/codebuild/standard:5.0"
    type                        = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"
    
    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = var.aws_region
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec.yml"
  }

  tags = {
    Environment = "Production"
  }
}
