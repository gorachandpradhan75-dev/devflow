# DevFlow - DevOps Deployment & Service Management Platform

**Build. Containerize. Deploy.**

DevFlow is a web dashboard for managing services, deployments, CI/CD builds and Docker containers.
It is an academic project demonstrating **GitHub -> Jenkins -> Automated Tests -> Docker Build -> Docker Deployment -> Running Web App**.

## Architecture

```
Browser --> frontend (Nginx :8095) --/api--> backend (Flask + Gunicorn :5000) --> db (PostgreSQL)
                         all three containers share the Docker network "devflow-net"

GitHub push --> Jenkins --> pytest --> docker compose build --> docker compose up -d --> /api/health
```

## Technologies

| Layer    | Tools                                   |
|----------|-----------------------------------------|
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js |
| Backend  | Python 3.12, Flask, Flask-SQLAlchemy, Gunicorn |
| Database | PostgreSQL 16                           |
| DevOps   | Docker, Docker Compose, Jenkins, GitHub |

## Run with Docker (recommended)

```bash
cp .env.example .env          # then edit POSTGRES_PASSWORD
docker compose up --build
```

Open http://localhost:8095 (dashboard) and http://localhost:5000/api/health (API).

Useful commands: `docker compose ps`, `docker images`, `docker compose logs backend`, `docker compose down` (add `-v` to also delete the database volume).

`database/init.sql` creates the tables only. There is **no demo data**: a fresh install shows 0 services, 0 deployments and 0 builds.

### Reset the database

`init.sql` runs only when the database volume is first created, so a volume from an older (seeded) version keeps its old rows until you delete it:

```bash
docker compose down -v        # stops containers AND deletes the pgdata volume
docker compose up --build     # recreates an empty database
```

### Where real data comes from

- **Services**: created, edited and deleted on the Services page (stored in PostgreSQL).
- **Deployments**: created when you press *Deploy* on a service (`POST /api/services/<id>/deploy`).
- **Builds**: created by the Jenkinsfile, which posts the result to `POST /api/pipelines` after a successful run.
- **Docker page**: shows the Docker Compose configuration; only the backend and database status are checked live.

## Run tests

```bash
python3 -m venv venv && source venv/bin/activate
pip install -r backend/requirements-dev.txt
pytest tests -v
```

Tests use an in-memory SQLite database, so no PostgreSQL is needed to run them.

## Jenkins pipeline

The `Jenkinsfile` has six stages: **Checkout -> Install Dependencies -> Run Tests -> Build Docker Images -> Deploy -> Health Check**.
A failing test stops the pipeline before any image is built. After a successful run, the build is posted to `/api/pipelines` and shows on the CI/CD page.

Jenkins setup:
1. Install Jenkins on a machine that also has Docker (with the compose plugin), Python 3 with `venv`, and curl.
2. Add the `jenkins` user to the `docker` group and restart Jenkins.
3. Create a **Pipeline** job, choose *Pipeline script from SCM*, enter your GitHub repository URL, and set the script path to `Jenkinsfile`.
4. Optional: add a GitHub webhook (`http://<jenkins-host>:8080/github-webhook/`) and tick *GitHub hook trigger* for automatic builds.
5. The pipeline copies `.env.example` to `.env` if none exists. For real use, create `.env` in the Jenkins workspace with your own password.

If Jenkins itself runs in a container, change `BACKEND_URL` in the Jenkinsfile so it can reach the backend port.

## REST API

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET/POST | `/api/services` | List / create services |
| GET/PUT/DELETE | `/api/services/<id>` | Read / update / delete a service |
| POST | `/api/services/<id>/deploy` | Record a deployment |
| GET | `/api/deployments` | Deployment history |
| GET/POST | `/api/pipelines` | CI/CD build records |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/docker` | Container information |
| GET | `/api/health` | App and database health |

## Security notes

- Secrets are read from environment variables (`.env` is git-ignored).
- All input is validated; invalid input returns 400, duplicates 409, missing items 404.
- Nginx proxies `/api`, so the browser uses a single origin and CORS is not enabled.
- Unexpected errors return a generic message; database details are never exposed.
- The backend container runs as a non-root user.

## Project structure

```
devflow/
├── backend/        Flask app (app.py, config.py, models/, routes/, services/)
├── frontend/       Dashboard (index.html, css/, js/), nginx.conf, Dockerfile
├── database/       init.sql (schema + sample data)
├── tests/          pytest API tests
├── Dockerfile      Backend image
├── docker-compose.yml
├── Jenkinsfile
├── .env.example
└── README.md
```

## Future scope

Authentication, real Docker/Jenkins API integration, Kubernetes deployment, monitoring dashboards.
