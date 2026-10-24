# Automating Hybrid CI/CD Pipelines with GitHub Actions and AWS CodePipeline

---

## Metadata

* **Title**: Automating Hybrid CI/CD Pipelines with GitHub Actions and AWS CodePipeline
* **Description**: Learn how to structure a continuous delivery (CD) pipeline by combining GitHub Actions for code integration with AWS CodePipeline and AWS CodeDeploy for automated, secure, and zero-downtime deployments of FastAPI and Vue.js applications.
* **Tags**: `AWS` `CI/CD` `GitHub Actions` `CodePipeline` `Python` `DevOps`

---

## Body

### Introduction

In modern software engineering, automating the software delivery lifecycle is no longer optional—it is a core requirement. Ensuring that code changes are validated, tested, and deployed to staging or production environments consistently reduces human error and significantly speeds up time-to-value.

While **GitHub Actions** is widely popular for Continuous Integration (CI), AWS offers robust native services like **AWS CodePipeline**, **AWS CodeBuild**, and **AWS CodeDeploy** that integrate seamlessly with cloud infrastructure (whether hosted on EC2 instances, ECS/EKS containers, or Serverless Lambda functions).

In this article, we will explore how to combine the best of both worlds: leveraging **GitHub Actions** for the Continuous Integration (CI) stage and **AWS CodePipeline** to orchestrate Continuous Deployment (CD) for a full-stack **Python/FastAPI** REST API and **Vue.js** frontend.

---

### Architecture Overview

The automated workflow follows these steps:

1. **Development & Push**: The developer pushes code or opens a Pull Request on the GitHub repository.
2. **CI in GitHub Actions**:
   * Execution of linters, unit tests, and integration tests.
   * Compiling the application and generating the build artifact.
   * Secure authentication with AWS via **OIDC** (eliminating long-lived static credentials).
   * Uploading the build artifact to a dedicated **Amazon S3** release bucket.
3. **CD in AWS CodePipeline**:
   * CodePipeline detects the new object version in S3 (trigger).
   * Initiates the deployment stage by invoking **AWS CodeDeploy** or updating the target service (ECS/EC2/Lambda).
   * Performs the deployment using zero-downtime strategies such as *Rolling Updates* or *Blue/Green*.

```
[ Developer ] --(git push)--> [ GitHub Repository ]
                                     |
                                     v
                           [ GitHub Actions CI ]
                         (Test, Build & OIDC Auth)
                                     |
                                     v
                           [ Amazon S3 Bucket ]
                                     |
                                     v
                          [ AWS CodePipeline CD ]
                                     |
                                     v
                           [ AWS CodeDeploy ]
                                     |
                         +-----------+-----------+
                         |                       |
                         v                       v
                   [ EC2 / ECS ]           [ Serverless ]
```

---

### 🔗 Complete Sample Application & Hands-On Repository

To provide a real-world scenario, the accompanying GitHub repository contains a full-stack **Pets & Owners Management System**:

* **Backend**: Python 3.11 with **FastAPI** (REST API, Pydantic validation, OpenAPI docs).
* **Frontend**: **Vue.js 3** utilizing `localStorage` for offline persistence and light-speed reactivity without complex authentication overhead.
* **Local Development**: Smart startup script (`check_docker.py`) that validates if **Docker Desktop** daemon is running before orchestrating `docker-compose`.

👉 **[Access the GitHub Repository: aws-hybrid-cicd-demo](https://github.com/your-username/aws-hybrid-cicd-demo)**

---

### Essential CI/CD Best Practices on AWS

#### 1. Secure Authentication without Static Access Keys (OIDC)
Avoid storing `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` in GitHub secrets. The AWS-recommended practice is to configure an **OpenID Connect (OIDC)** identity provider within AWS IAM. This allows GitHub Actions to assume a short-lived IAM Role scoped strictly to the required permissions.

Here is the CloudFormation template snippet (`iac/template.yaml`) used to provision the OIDC role:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: OIDC Provider and IAM Role for GitHub Actions integration.

Parameters:
  GitHubOrg:
    Type: String
    Default: 'your-github-username'
  RepositoryName:
    Type: String
    Default: 'aws-hybrid-cicd-demo'

Resources:
  GitHubOIDCProvider:
    Type: AWS::IAM::OIDCProvider
    Properties:
      Url: https://token.actions.githubusercontent.com
      ClientIdList:
        - sts.amazonaws.com
      ThumbprintList:
        - 6938fd4d98bab03faadb97b34396831e3780aea1

  GitHubActionsRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: GitHubActionsCodePipelineRole
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Federated: !Ref GitHubOIDCProvider
            Action: sts:AssumeRoleWithWebIdentity
            Condition:
              StringEquals:
                token.actions.githubusercontent.com:aud: sts.amazonaws.com
              StringLike:
                token.actions.githubusercontent.com:sub: !Sub repo:${GitHubOrg}/${RepositoryName}:*
      Policies:
        - PolicyName: S3ArtifactUploadPolicy
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:PutObject
                  - s3:GetObject
                Resource: 'arn:aws:s3:::my-aws-deploy-bucket/*'
```

#### 2. Artifact Immutability
Every build generated by the CI pipeline must produce a unique artifact (tagged with the commit hash or semantic release tag). Never reuse mutable artifacts across environments.

#### 3. Zero-Downtime Deployment Strategies
For high-availability REST APIs, configure AWS CodeDeploy using **Blue/Green** or **Canary** deployment strategies. This ensures incoming traffic is redirected to the new release only after health checks pass successfully.

#### 4. Secrets and Environment Variable Management
Sensitive database credentials and external API keys should never be hardcoded into the application repository. Use **AWS Secrets Manager** or **AWS Systems Manager Parameter Store** to inject secrets at runtime.

---

### Practical Example: GitHub Actions Workflow

Below is an example `.github/workflows/deploy.yml` workflow file designed to test, build, and package the Python/FastAPI artifact for AWS deployment:

```yaml
name: CI/CD Pipeline

on:
  push:
    branches:
      - main

permissions:
  id-token: write
  contents: read

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4

      - name: Set up Python 3.11
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install Dependencies and Run Tests
        run: |
          python -m pip install --upgrade pip
          pip install -r backend/requirements.txt pytest
          pytest backend/tests

      - name: Authenticate to AWS via OIDC
        uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/GitHubActionsCodePipelineRole
          aws-region: us-east-1

      - name: Package and Upload Artifact to Amazon S3
        run: |
          zip -r release.zip . -x "*.git*" "frontend/node_modules/*"
          aws s3 cp release.zip s3://my-aws-deploy-bucket/releases/app-${{ github.sha }}.zip
```

---

### Local Ecosystem Orchestration Script

To make developer onboarding seamless, the repository includes a Python script (`scripts/check_docker.py`) that checks if Docker Desktop is operational before bringing up the containers:

```python
import subprocess
import sys
import time

def is_docker_running():
    try:
        result = subprocess.run(["docker", "info"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

def main():
    print("🔍 Checking Docker Desktop status...")
    if not is_docker_running():
        print("⚠️ Docker Desktop is not running or initializing.")
        print("🚀 Waiting for Docker daemon...")
        
        retries = 5
        while retries > 0:
            time.sleep(3)
            if is_docker_running():
                print("✅ Docker Daemon active!")
                break
            retries -= 1
        else:
            print("❌ Error: Please start Docker Desktop and try again.")
            sys.exit(1)
    else:
        print("✅ Docker Desktop is running.")

    print("📦 Spinning up ecosystem containers with docker-compose...")
    subprocess.run(["docker-compose", "up", "-d", "--build"])

if __name__ == "__main__":
    main()
```

---

### AWS CodePipeline Configuration

In the AWS Management Console:

1. **Source Stage**: Set the source to monitor the S3 bucket where `release.zip` is uploaded by GitHub Actions.
2. **Deploy Stage**: Select your target deployment mechanism:
   * **AWS CodeDeploy** for EC2 or On-Premises targets using `appspec.yml`.
   * **Amazon ECS** for containerized deployments.
   * **AWS CloudFormation / SAM** for Serverless architectures.

---

### Conclusion

Combining **GitHub Actions** for rapid testing and artifact generation with **AWS CodePipeline** for cloud-native orchestration and governance yields a modern, scalable, and secure deployment strategy. Adopting this hybrid pattern significantly decreases cycle time while keeping production environments resilient.

---