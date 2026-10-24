# Operations Runbook

This runbook covers GitHub Actions authentication to AWS with OpenID Connect
(OIDC) and local startup of the pet-owner application.

## 1. Prerequisites

- An AWS account and permission to create/manage the CloudFormation, IAM, and
  S3 resources described below.
- A GitHub repository containing this project and the workflow at
  `.github/workflows/deploy.yml`.
- For local execution: Docker Desktop/Engine and the legacy `docker-compose`
  command used by `scripts/check_docker.py`.

## 2. Provision the AWS OIDC role and artifact bucket

The CloudFormation template at `iac/template.yaml` provisions:

- A GitHub Actions OIDC identity provider.
- An S3 artifact bucket with versioning enabled.
- An IAM role named `GitHubActionsCodePipelineRole`, trusted for the configured
  GitHub organization and repository.
- Permissions to read and write objects in the configured bucket.

Before deployment, review the template parameters and defaults:

| Parameter | Default | Purpose |
| --- | --- | --- |
| `GitHubOrg` | `belarminon` | GitHub organization or account in the OIDC trust condition |
| `RepositoryName` | `aws-hybrid-cicd-demo` | Repository in the OIDC trust condition |
| `ArtifactBucketName` | `aws-hybrid-cicd-artifacts-bucket` | S3 bucket receiving release archives |

Use a globally unique bucket name and the same AWS region that you intend to
use in the workflow. Deploy the template, for example:

```bash
aws cloudformation deploy \
  --template-file iac/template.yaml \
  --stack-name aws-hybrid-cicd-demo-oidc \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    GitHubOrg=YOUR_GITHUB_ORG \
    RepositoryName=YOUR_REPOSITORY \
    ArtifactBucketName=YOUR_GLOBALLY_UNIQUE_BUCKET
```

If the GitHub OIDC provider already exists in the AWS account, the template may
fail because IAM allows only one provider for a given issuer URL per account.
In that case, use the existing provider and adapt the template/role trust
configuration rather than trying to create a duplicate.

After the stack reaches `CREATE_COMPLETE` or `UPDATE_COMPLETE`, find the role
ARN in the IAM console under **Roles** → `GitHubActionsCodePipelineRole`.
The ARN has this form:

```text
arn:aws:iam::AWS_ACCOUNT_ID:role/GitHubActionsCodePipelineRole
```

## 3. Configure GitHub Actions repository variables

Open the repository in GitHub and go to:

**Settings** → **Secrets and variables** → **Actions** → **Variables**.

Add these **repository variables**:

| Variable | Example value | Notes |
| --- | --- | --- |
| `AWS_REGION` | `us-east-1` | Must be the region containing the artifact bucket |
| `AWS_ROLE_ARN` | `arn:aws:iam::123456789012:role/GitHubActionsCodePipelineRole` | Replace the example account ID with the real role ARN |
| `S3_BUCKET_NAME` | `aws-hybrid-cicd-artifacts-bucket` | Must match the deployed bucket name |

The IAM role ARN is not region-specific; the S3 bucket is. Set `AWS_REGION` to
the region where the bucket was created.

These values are configuration, not credentials. Do **not** create or store
`AWS_ACCESS_KEY_ID` or `AWS_SECRET_ACCESS_KEY` for this workflow. GitHub
requests a short-lived OIDC token and the AWS credentials action exchanges it
for temporary AWS credentials.

The workflow at `.github/workflows/deploy.yml` runs on pushes to `main`. It
requests the OIDC token, assumes `AWS_ROLE_ARN`, and uploads an archive to:

```text
s3://S3_BUCKET_NAME/releases/app-GITHUB_COMMIT_SHA.zip
```

The current workflow packages the repository and uploads it to S3; it does not
start an AWS CodeDeploy deployment. `appspec.yml` and its hooks are present,
but a CodeDeploy application/deployment group and workflow deployment step
would need to be configured separately.

## 4. Run the application locally in isolation

Run commands from the repository root. The helper script waits briefly for the
Docker daemon if it is not ready, then builds and starts this Compose project
with the fixed project name `aws-pet-owner-app`:

```bash
python scripts/check_docker.py
```

The script requires the `docker-compose` executable (Compose v1-style command).
Check that the containers are running:

```bash
docker ps --filter "name=pet-owner"
```

The Compose file assigns the container names `pet-owner-backend` and
`pet-owner-frontend`. The project name also scopes Compose networks and other
project-managed resources.

Open:

- Frontend: <http://localhost:3000>
- Backend health: <http://localhost:8000/health>
- Backend API documentation: <http://localhost:8000/docs>

Stop only this application using the same project name:

```bash
docker-compose -p aws-pet-owner-app down --remove-orphans
```

This is the same project identifier used by `scripts/check_docker.py` and
`scripts/app_stop.sh`. Do not omit `-p aws-pet-owner-app` when stopping the
project if you need to ensure Compose targets this named project.

## 5. Operational notes

- Ports `3000` and `8000` must be available on the host.
- The frontend saves its data in browser `localStorage`; it does not currently
  call the backend API.
- The backend stores data in process memory and loses it when its container
  restarts or is recreated.
- The frontend container runs the Vite development server, not a production
  static web server.
- The AWS workflow uploads an artifact only. Confirm the workflow run and the
  corresponding object in the S3 bucket to verify that step.
