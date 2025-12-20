provider "aws" {
  region = "us-west-2"
}

# AWS EKS Cluster Definition
resource "aws_eks_cluster" "zeus_cluster" {
  name     = "zeus-prod-cluster"
  role_arn = aws_iam_role.zeus_role.arn

  vpc_config {
    subnet_ids = [aws_subnet.main.id]
  }
}

# AWS Lambda Function for serverless automation
resource "aws_lambda_function" "zeus_monitor" {
  filename      = "lambda_function_payload.zip"
  function_name = "zeus_resource_monitor"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "app.lambda_handler"
  runtime       = "python3.9"
}

# EC2 Instance for legacy processing
resource "aws_instance" "worker_node" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name = "Zeus-Worker"
  }
}
