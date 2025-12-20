# Project Zeus ⚡
### Cloud Infrastructure Automation & DevOps Pipeline

**Project Zeus** is a comprehensive DevOps initiative designed to automate the provisioning, deployment, and monitoring of cloud-native applications. It utilizes **Infrastructure as Code (IaC)** principles to manage **AWS** resources and employs **Azure DevOps** for a robust CI/CD pipeline.

---

### 🛠 Tech Stack
* **Cloud Provider:** AWS (EKS, Lambda, EC2, S3)
* **CI/CD:** Azure DevOps Pipelines
* **Containerization:** Docker & Kubernetes
* **Infrastructure as Code:** Terraform
* **Scripting:** Python 3.9 & Bash (Linux)

### 📂 Repository Structure
* `/infrastructure`: Terraform configurations for provisioning **AWS EKS** clusters and **Lambda** functions.
* `/src`: The core monitoring service built with **Python**.
* `/pipelines`: YAML configuration for **Azure DevOps** automated build triggers.
* `/scripts`: **Bash** scripts for Linux server maintenance and health checks.

### 🚀 Key Features
1.  **Serverless Automation:** Python scripts deployed on AWS Lambda to monitor resource usage and reduce costs.
2.  **Container Orchestration:** Dockerized application deployed to a managed Kubernetes (EKS) cluster.
3.  **Automated CI/CD:** Commits to the `main` branch trigger an Azure Pipeline that builds the Docker image and runs unit tests.

### 💻 How to Run
To build the container locally:
```bash
docker build -t zeus-monitor .
docker run -p 80:80 zeus-monitor
