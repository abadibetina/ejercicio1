# Hello DevOps

A simple Flask web app with a Postgres database, containerized with Docker.

## Endpoints

| Method | Path        | Response                          |
| ------ | ----------- | --------------------------------- |
| GET    | `/`         | `{"message": "Hello DevOps"}`     |
| GET    | `/health`   | `{"status": "ok"}`                |
| GET    | `/db-check` | `{"database": "ok"}` (503 on error) |

## Requirements

- [Python 3.14](https://www.python.org/downloads/) (use the `py` launcher on Windows)
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose (for the containerized setup)

> **Windows note:** the bare `python` / `pip` commands may resolve to the
> Microsoft Store stub and fail. Use the `py` launcher instead: `py -m pip ...`,
> `py -m pytest ...`, `py app.py`.

## Install the requirements

```powershell
py -m pip install -r requirements.txt
```

## Run the app locally

```powershell
py app.py
```

The app listens on http://localhost:5000. Note that `/db-check` needs a reachable
Postgres database (see the Docker section below) to return `ok`.

Quick check from another terminal:

```powershell
curl http://localhost:5000/
curl http://localhost:5000/health
curl http://localhost:5000/db-check
```

## Run the tests

```powershell
py -m pytest -v
```

The database tests are mocked, so no running Postgres is required.

Useful variations:

```powershell
py -m pytest test_app.py::test_health   # run a single test
py -m pytest -k db_check                # run tests matching a keyword
py -m pytest -q                         # compact output
```

## Build and run with Docker

The recommended way is Docker Compose, which starts both the web app and the
Postgres database and wires them together:

```powershell
docker compose up --build
```

Then visit:

- http://localhost:5000/
- http://localhost:5000/health
- http://localhost:5000/db-check

Stop and remove the containers:

```powershell
docker compose down
```

To also delete the database volume:

```powershell
docker compose down -v
```

### Build / run only the app image (without Compose)

```powershell
docker build -t hello-devops .
docker run -p 5000:5000 hello-devops
```

Run the tests inside the container:

```powershell
docker compose run --rm web pytest -v
```

## Continuous Integration (GitHub Actions)

The pipeline is defined in [`.github/workflows/ci.yml`](.github/workflows/ci.yml)
and runs automatically on **every push** and on **every pull request**.

### What the pipeline does

It runs two jobs on GitHub's hosted Ubuntu runners:

1. **`test`** — verifies the code works:
   - Checks out the repository.
   - Sets up Python 3.14 (with pip caching to speed up repeat runs).
   - Installs the dependencies from `requirements.txt`.
   - Runs the full test suite with `pytest -v`.

2. **`docker-build`** — verifies the app still packages correctly:
   - Runs only **after** the `test` job succeeds (`needs: test`), so a broken
     build never gets to this stage.
   - Builds the Docker image from the `Dockerfile`.

If any step fails (a test breaks, a dependency won't install, or the image won't
build), the workflow fails and GitHub marks the commit/PR with a red ❌. When
everything passes you get a green ✔, which gives you confidence before merging.

> The tests mock the database, so the pipeline does **not** need a running
> Postgres service — it stays fast and self-contained.

### Where to see the results

Push the repository to GitHub, then open the **Actions** tab. Each push/PR shows
a run with the live logs of every step.

## Project structure

```
.
├── .github/
│   └── workflows/
│       └── ci.yml        # GitHub Actions CI pipeline
├── app.py                # Flask application
├── test_app.py           # Tests for each endpoint
├── requirements.txt      # Python dependencies
├── Dockerfile            # App image definition
├── docker-compose.yml    # App + Postgres orchestration
└── README.md
```
