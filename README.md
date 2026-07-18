# Hello DevOps

A simple Flask web app backed by a Postgres database and a Redis cache,
containerized with Docker and split across isolated networks.

## Summary

A hands-on DevOps practice project: a tiny Flask API is the vehicle for
demonstrating real-world container practices. It runs three services with
Docker Compose (`web` + Postgres + Redis), isolates the data tier on an
internal-only network so it can't be reached from the host, adds health checks
and a `unless-stopped` restart policy for resilience, ships unit tests for every
endpoint, and wires it all into a GitHub Actions pipeline that tests, builds,
and verifies the full stack boots and connects end to end.

## Endpoints

| Method | Path           | Response                             |
| ------ | -------------- | ------------------------------------ |
| GET    | `/`            | `{"message": "Hello DevOps"}`        |
| GET    | `/health`      | `{"status": "ok"}`                   |
| GET    | `/db-check`    | `{"database": "ok"}` (503 on error)  |
| GET    | `/cache-check` | `{"cache": "ok"}` (503 on error)     |

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

## Network architecture

The services are split across two Docker networks so that the data tier is
never directly reachable from the outside — only the web app is.

```
                    ┌─────────────────────────────────────┐
   User / host      │              frontend               │
  (localhost:5000) ─┼──▶ [ web ]                           │  normal network
                    │       │                              │
                    └───────┼──────────────────────────────┘
                            │
                    ┌───────┼──────────────────────────────┐
                    │       ▼      backend (internal)       │  internal: true
                    │   [ web ] ──▶ [ db ]      [ cache ]   │  (no internet,
                    │                                       │   no host access)
                    └───────────────────────────────────────┘
```

- **`frontend`** — public edge. Only `web` is attached here, and it is the
  only service that publishes a port (`5000`) to the host. It is the single
  entry point for users.
- **`backend`** — private tier, marked `internal: true` (no route to the
  internet, unreachable from the host). `web`, `db` and `cache` live here.
  `db` and `cache` are attached **only** to this network and publish **no
  ports**.

Why this matters:

- **Users cannot talk to Postgres or Redis directly.** They have no published
  ports and are not on `frontend`, so `curl localhost:5432` from the host fails.
  All access is forced through the `web` app.
- **`web` is the only bridge.** It sits on both networks: it faces users on
  `frontend` and reaches the data tier on `backend`.
- **Blast-radius containment.** Because `backend` is `internal`, even a
  compromised `db`/`cache` cannot reach the internet.

### How to prove the isolation locally

Start the full stack:

```powershell
docker compose up -d --build
```

**1. The app can reach the data tier internally** (through the `web` bridge on
the `backend` network):

```powershell
curl http://localhost:5000/db-check      # {"database":"ok"}
curl http://localhost:5000/cache-check   # {"cache":"ok"}
```

**2. The host cannot reach the data tier directly** (no published ports, not on
`frontend`):

```powershell
curl http://localhost:5432    # Postgres: connection refused
curl http://localhost:6379    # Redis: connection refused
```

**3. Inspect which services sit on each network** — `db` and `cache` should
appear only under `backend`, and `web` under both:

```powershell
docker network inspect ejercicio1_backend
docker network inspect ejercicio1_frontend
```

> Compose prefixes network names with the project folder (e.g.
> `ejercicio1_backend`). Run `docker network ls` to see the exact names.

Tear everything down when done:

```powershell
docker compose down
```

## Resilience (restart policy)

All three services (`web`, `db`, `cache`) use `restart: unless-stopped`. This
means Docker automatically brings a container back up if it crashes or after the
host/Docker daemon reboots — but it does **not** restart a container that you
stopped on purpose (e.g. `docker compose stop`), so maintenance is respected.

| Policy            | On crash | After host reboot | After manual stop |
| ----------------- | -------- | ----------------- | ----------------- |
| `no`              | ❌       | ❌                | ❌                |
| `on-failure`      | ✅       | only if running   | ❌                |
| `always`          | ✅       | ✅                | ✅ (unwanted)     |
| `unless-stopped`  | ✅       | ✅                | ❌                |

`unless-stopped` is chosen over `always` because it respects a deliberate stop,
and over `on-failure` because these are long-running services that should also
survive clean reboots.

> In CI the stack is started and torn down within a single run, so the restart
> policy has no effect there — it matters on a real, long-lived host.

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
├── docker-compose.yml    # web + Postgres + Redis, split across two networks
└── README.md
```
