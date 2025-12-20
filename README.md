# Project Zeus ⚡
### Cloud Infrastructure Automation & DevOps Engine

**Project Zeus** is a comprehensive engineering initiative designed to eliminate cloud resource waste. It acts as an **Infrastructure Engine** that automates the provisioning, monitoring, and lifecycle management of cloud resources.

It is built with **AWS (Lambda, EKS, S3)**, defined via **Terraform**, containerized with **Docker**, and managed through **Azure DevOps** and **AWS CodePipeline**.

![Project Zeus Dashboard](./demo.png)

### 📋 Prerequisites (Production)
While the Simulation Mode runs on any machine with Docker, deploying to a live cloud environment requires:
1.  **AWS Account:** Active account with AdministratorAccess.
2.  **AWS CLI:** Configured locally via `aws configure`.
3.  **Terraform CLI:** Installed (v1.0+).
4.  **Azure DevOps:** An active organization with a **Service Connection** configured to your AWS account (to authorize the pipeline).

---

---

### 🏗️ Architecture & Components
This project is a modular system composed of four distinct pillars. Each component corresponds to specific infrastructure requirements defined in the architecture.

#### 1. Cloud Infrastructure (AWS & Terraform)
* **Component:** `/infrastructure`
* **Function:** Contains **Terraform (IaC)** blueprints that programmatically define the data center.
    * `main.tf`: Provisions **EKS Clusters** for high-availability hosting, **S3 Buckets** for log retention, and **EC2** compute capacity.
    * `variables.tf`: Configures region-specific settings (e.g., `us-west-2`) to ensure idempotency.
* **Usage:** Run `terraform plan` to view the infrastructure blueprint before deployment.

#### 2. DevOps & CI/CD (Azure & CodePipeline)
* **Component:** `/pipelines` & `/infrastructure`
* **Function:** A hybrid automation strategy.
    * `azure-pipelines.yml`: Triggers on git commits to run unit tests and build Docker images.
    * **AWS CodePipeline:** Defined in Terraform to manage the deployment of artifacts from S3 to the production EKS cluster.
* **Usage:** Connect this repository to Azure DevOps to enable automated "Commit-to-Cloud" deployments.

#### 3. Monitoring & Observability (Grafana & Python)
* **Component:** `/monitoring` & `/src`
* **Function:** Real-time tracking of system health.
    * `src/app.py`: A **Flask** microservice acting as the control plane. In "Simulation Mode," it generates telemetry; in Production, it connects to **AWS CloudWatch**.
    * `monitoring/grafana_dashboard.json`: JSON configuration for importing visual metrics into Grafana.

#### 4. Containerization (Docker)
* **Component:** `Dockerfile`
* **Function:** A multi-stage build script that packages the Python 3.9 runtime and installs dependencies.
* **Usage:** Ensures the application runs identically on a local developer laptop and a production Kubernetes node.

---

### 🎮 Modes of Operation
Project Zeus is designed to be modular. You can run it in three different modes depending on your environment.

#### Mode 1: Simulation (Default)
Generates mock telemetry data. Useful for frontend development and UI testing without needing access to system resources.
* **Usage:** `docker run -p 8080:80 zeus-monitor`

#### Mode 2: Local System Monitor (Real Data)
Connects to the host Linux kernel to visualize actual CPU and Memory usage of the local machine.
* **Requirement:** Add `psutil` to `requirements.txt`.
* **Why use this:** Proves the application logic works with real-time, fluctuating data streams.

#### Mode 3: Cloud Production (AWS)
Connects to AWS CloudWatch to monitor remote EKS clusters.
* **Requirement:** AWS Credentials configured via IAM.
* **Code Change:** Update `src/app.py` to use the `boto3` client.

---



### 🛡️ License
Distributed under the MIT License. See `LICENSE` for more information.
