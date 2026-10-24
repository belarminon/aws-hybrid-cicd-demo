# Troubleshooting

## GitHub Actions cannot assume the AWS role

**Symptoms:** The workflow fails in `Configure AWS credentials` with an
`AccessDenied`, `Not authorized to perform sts:AssumeRoleWithWebIdentity`, or
OIDC provider error.

Check:

1. The workflow has `permissions: id-token: write` (the repository workflow
   currently declares this permission).
2. `AWS_ROLE_ARN` is the ARN of `GitHubActionsCodePipelineRole` in the intended
   AWS account.
3. `AWS_REGION` is the region where the target bucket is configured.
4. The IAM role trust policy's GitHub organization and repository match the
   workflow's actual repository. The defaults in `iac/template.yaml` are
   `belarminon/aws-hybrid-cicd-demo`.
5. The IAM OIDC provider exists for
   `https://token.actions.githubusercontent.com` and uses the
   `sts.amazonaws.com` audience.
6. The workflow is running from a ref allowed by the role's `sub` condition.
   The template currently allows any subject under the configured repository
   using a wildcard; tighten this condition if only specific branches should
   be trusted.

No long-lived AWS access key should be necessary for this workflow.

## GitHub Actions cannot upload the release archive

**Symptoms:** Authentication succeeds, but `aws s3 cp` returns
`NoSuchBucket`, `AccessDenied`, or a region-related error.

Check:

- `S3_BUCKET_NAME` exactly matches the bucket provisioned by CloudFormation.
- `AWS_REGION` is the bucket's region.
- The role policy permits `s3:PutObject` for
  `arn:aws:s3:::BUCKET_NAME/*`. The provided template grants this object-level
  action.
- The bucket name was available globally when the stack was created.
- The IAM role and bucket are in the account expected by `AWS_ROLE_ARN`.

The workflow uploads to `releases/app-<commit-sha>.zip`; it does not require a
static AWS key.

## Workflow succeeds but the application was not deployed

The current `.github/workflows/deploy.yml` packages the repository and uploads
the archive to S3. It does not invoke CodeDeploy. The presence of `appspec.yml`
alone does not deploy the application. Configure a CodeDeploy application and
deployment group, grant the workflow role the required CodeDeploy permissions,
and add a deployment step if automated instance deployment is required.

## Docker daemon is unavailable

**Symptoms:** `python scripts/check_docker.py` reports that Docker is not
running or exits after its retries.

1. Start Docker Desktop or the Docker Engine service.
2. Confirm the active Docker context is usable with `docker info`.
3. Retry `python scripts/check_docker.py`.
4. Verify the `docker-compose` command is installed and available on `PATH`:

   ```bash
   docker-compose version
   ```

The helper waits for up to five retries, sleeping three seconds between
attempts. It checks the Docker daemon but invokes the separate
`docker-compose` command to start the project.

## Compose reports that the compose command is missing

The local helper and CodeDeploy hooks use `docker-compose`, not
`docker compose`. Install a compatible Compose v1 executable or update the
scripts to the Compose v2 plugin command before relying on v2-only installations.
The helper currently checks the daemon but does not check whether
`docker-compose` is installed, so a missing executable will cause startup to
fail.

## Ports 3000 or 8000 are already allocated

**Symptoms:** Docker cannot bind a host port during startup.

Find which process or container is using the port, then stop only that process
or container if appropriate. Alternatively, change the host-side port mapping
in `docker-compose.yml` while keeping the container-side port unchanged. For
example, `3001:3000` publishes the frontend on host port `3001`.

## The app starts but containers are not visible under the expected project

The helper starts Compose with project name `aws-pet-owner-app`, and the Compose
file also defines the explicit container names `pet-owner-backend` and
`pet-owner-frontend`. Check them with:

```bash
docker ps --filter "name=pet-owner"
docker-compose -p aws-pet-owner-app ps
```

If starting or stopping manually, use the same project name:

```bash
docker-compose -p aws-pet-owner-app up -d --build
docker-compose -p aws-pet-owner-app down --remove-orphans
```

Explicit container names are global to the Docker host and cannot be reused by
a second copy of this app on that host, even if the second Compose project name
is different. Remove/stop the existing pet-owner containers or remove the
`container_name` settings if multiple concurrent copies are required.

## Data is missing after a restart

This is expected for the current demo:

- Frontend data is stored in the browser's `localStorage`; use the same browser
  profile and origin to see that data. Clearing site data removes it.
- Backend data is kept in memory and resets whenever the API process restarts.
- The frontend and backend currently do not synchronize records.

Persistent, shared data requires implementing durable database storage and
connecting the frontend to the API.
