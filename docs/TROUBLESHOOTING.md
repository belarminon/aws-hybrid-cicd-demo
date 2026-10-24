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
4. Verify that either supported Compose command is available:

   ```bash
   docker compose version
   ```

The helper waits for up to five retries, sleeping three seconds between
attempts. It supports `docker compose` and the standalone `docker-compose`
command.

## Compose reports that the compose command is missing

The startup helper and CodeDeploy hooks support both the Docker Compose v2
plugin (`docker compose`) and the standalone `docker-compose` command. Install
either one and make sure it is available on `PATH`.

## Bash reports `app_start.sh: command not found`

Bash does not search the current directory for commands by default. From the
`scripts` directory, invoke the file with an explicit relative path:

```bash
bash ./app_start.sh
```

On a Linux host, if the script has its executable bit set, this also works:

```bash
./app_start.sh
```

`app_start.sh` now locates `check_docker.py` relative to itself, so it can be
run from the repository's `scripts` directory in Git Bash or Linux. From the
repository root, it can also be run as:

```bash
bash scripts/app_start.sh
```

The script requires Python 3, Docker, and either `docker compose` or
`docker-compose`. It no longer changes to a hard-coded Linux checkout path.

## Ports 3000 or 8000 are already allocated

The startup helper checks whether host ports `3000` (frontend) and `8000`
(backend) are available. If either is occupied, it selects the next available
port in that service's range (`3000`-`3099` for the frontend and `8000`-`8099`
for the backend) and prints the resulting URLs. It does not stop or alter the
process using the original port.

If all ports in a range are unavailable, the helper reports an error rather
than stopping another process. If Docker still reports a bind error after
selection, another process may have claimed that port between the check and
container startup. Retry the helper or set `FRONTEND_PORT` / `BACKEND_PORT`
manually when running Compose. The `docker-compose.yml` mappings use those
variables and default to ports `3000` and `8000`.

## The app starts but containers are not visible under the expected project

The helper starts Compose with project name `aws-pet-owner-app`, and the Compose
file also defines the explicit container names `pet-owner-backend` and
`pet-owner-frontend`. Check them with:

```bash
docker ps --filter "name=pet-owner"
docker compose -p aws-pet-owner-app ps
```

If starting or stopping manually, use the same project name:

```bash
docker compose -p aws-pet-owner-app up -d --build
docker compose -p aws-pet-owner-app down --remove-orphans
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
