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

2. **`build-and-verify`** — verifies the app really runs end to end:
   - Runs only **after** the `test` job succeeds (`needs: test`), so a broken
     build never gets to this stage.
   - Builds the images and starts the containers with
     `docker compose up -d --build` (both the web app and Postgres).
   - **Health check:** polls `http://localhost:5000/health` for up to ~45s
     (15 attempts, 3s apart) until it responds `ok`. This confirms the app
     actually boots and serves traffic, not just that the image builds.
   - **Database connectivity check:** calls `http://localhost:5000/db-check`
     to confirm the running app can reach the Postgres container.
   - If anything fails, it prints the container logs (`docker compose logs`) to
     help debug.
   - Always tears the containers down at the end (`docker compose down`).

If any step fails (a test breaks, a dependency won't install, the image won't
build, or the running app doesn't answer the health check), the workflow fails
and GitHub marks the commit/PR with a red ❌. When everything passes you get a
green ✔, which gives you confidence before merging.

> The **unit tests** mock the database so they stay fast, but the
> `build-and-verify` job spins up a **real Postgres container**, so the health
> and DB-connectivity checks exercise the full stack.



Build de la imagen Docker ✅
Correr los tests ✅
Verificar que todo compila y funciona ✅
Levantar los contenedores temporalmente solo para testear ✅
Cuando el pipeline termina, todo se destruye solo — no necesitás parar nada

¿Podés acceder a la app que corre en el runner?
No, no podés abrir el browser y entrar a localhost:5000 porque esa máquina es temporal, no tiene IP pública, y desaparece cuando termina el pipeline.
Lo que sí podés hacer dentro del pipeline es:

Levantar los contenedores con docker compose up -d
Hacer un curl http://localhost:5000/health desde dentro del mismo runner
Verificar que responde correctamente
El runner para los contenedores solo al terminar

¿Y para practicar localmente sin AWS?
Para este ejercicio, el objetivo del pipeline no es dejar la app corriendo, sino verificar que:

1.La imagen buildea sin errores
2.Los tests pasan
3.Los contenedores levantan y responden

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
