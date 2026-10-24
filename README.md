# AWS Hybrid CI/CD Demo

A small pet-and-owner management application used to demonstrate a containerized
application and an AWS deployment foundation. The repository contains a Vue.js
frontend, a FastAPI REST API, Docker Compose configuration, and AWS/CodeDeploy
deployment files.

## Ecosystem at a glance

| Component | Technology | Purpose |
| --- | --- | --- |
| Frontend | Vue 3, Vite, Node.js 20 | Browser interface for registering owners and pets |
| Backend | Python 3.11, FastAPI, Pydantic, Uvicorn | REST API for owners and pets |
| Containers | Docker, Docker Compose | Build and run the frontend and backend services |
| AWS infrastructure | AWS CloudFormation, IAM, S3 | GitHub Actions OIDC provider, IAM role, and versioned artifact bucket |
| Instance deployment | AWS CodeDeploy | Copies the repository to the instance and runs Docker Compose lifecycle scripts |

### How the application currently handles data

The frontend and backend are separate demo implementations:

- The Vue interface saves owners and pets in the browser's `localStorage`.
  Data is local to that browser and remains there until it is cleared.
- The FastAPI service keeps its data in process memory. Data is lost when the
  service restarts.
- The frontend does not currently call the backend API. The two services can
  be run together, but their data is not synchronized.

## Repository layout

```text
.
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI routes
│   │   ├── database.py      # In-memory owner and pet storage
│   │   └── models.py        # Pydantic request/response schemas
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── public/
│   │   └── index.html      # Vite HTML entry point
│   ├── src/
│   │   ├── App.vue          # Pet and owner UI
│   │   └── main.js
│   ├── Dockerfile
│   ├── package.json
│   └── vite.config.js
├── iac/
│   └── template.yaml        # AWS OIDC, IAM role, and artifact bucket
├── scripts/
│   ├── app_start.sh         # CodeDeploy start hook
│   ├── app_stop.sh          # CodeDeploy stop hook
│   └── check_docker.py      # Docker availability check and compose launcher
├── appspec.yml              # AWS CodeDeploy application specification
├── docker-compose.yml
└── LICENSE                  # MIT License
```

## Run with Docker Compose

Requirements:

- Docker Engine/Desktop with Docker Compose available
- Ports `3000` and `8000` available on the host

From the repository root:

```bash
docker compose up --build
```

Open the frontend at <http://localhost:3000>. The backend API is available at
<http://localhost:8000>, with interactive API documentation at
<http://localhost:8000/docs>.

To stop the containers:

```bash
docker compose down
```

The Compose file builds both services from their respective directories and
publishes port `3000` for the frontend and `8000` for the API.

## Run services locally

### Backend

Requires Python 3.11 or a compatible version.

```bash
cd backend
python -m venv .venv
```

Activate the virtual environment, then install and run:

```bash
python -m pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On Windows PowerShell, activate the environment with:

```powershell
.\.venv\Scripts\Activate.ps1
```

### Frontend

Requires Node.js 20 or a compatible version.

```bash
cd frontend
npm install
npm run dev
```

Vite serves the interface at <http://localhost:3000>.

## Backend API

All data is held in memory and resets when the API process restarts.

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/health` | Health status |
| `GET` | `/owners` | List owners |
| `POST` | `/owners` | Create an owner |
| `DELETE` | `/owners/{owner_id}` | Delete an owner and the owner's pets |
| `GET` | `/pets` | List pets |
| `POST` | `/pets` | Create a pet; the referenced owner must exist |
| `DELETE` | `/pets/{pet_id}` | Delete a pet |

The API's owner fields are `name`, `email`, and optional `phone`. Pet fields
are `name`, `species`, optional `breed`, and `owner_id`. The API assigns IDs
when records are created.

## AWS deployment foundation

`iac/template.yaml` defines:

- An IAM OIDC identity provider for GitHub Actions.
- A versioned S3 bucket for artifacts.
- An IAM role trusted for tokens whose subject matches the configured GitHub
  organization and repository.
- An inline policy granting that role `s3:GetObject` and `s3:PutObject` access
  to objects in the configured artifact bucket.

The template parameters are `GitHubOrg`, `RepositoryName`, and
`ArtifactBucketName`. Review and customize these values and the IAM permissions
for your AWS account before deployment. The template provisions these resources;
it does not itself define a GitHub Actions workflow.

`appspec.yml` configures AWS CodeDeploy to copy the repository to
`/var/www/aws-hybrid-cicd-demo` on a Linux instance. The stop and start hooks
run `docker-compose down` and `docker-compose up -d --build` respectively.
The target instance must have Docker and Docker Compose installed, and the
deployment scripts expect the configured destination path.

## Dependencies

- Backend: FastAPI, Uvicorn, and Pydantic (see `backend/requirements.txt`).
- Frontend: Vue 3, Vite, and the Vue Vite plugin (see `frontend/package.json`).
- Container images: `python:3.11-slim` for the API and `node:20-alpine` for
  the Vite development server.