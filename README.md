# RailPulse

RailPulse is a railway ETA and delay-intelligence web application. It combines a static, framework-free frontend with a Python FastAPI service that validates train state, runs the existing ETA/delay ML pipeline, and persists train state and prediction history in MongoDB.

This is the **main repository overview** and the recommended clone-to-running guide. Component-specific API and implementation details remain in [railpulse-backend/README.md](railpulse-backend/README.md) and [railpulse-frontend/README.md](railpulse-frontend/README.md).

## Contents

- [What the application does](#what-the-application-does)
- [Architecture and data flow](#architecture-and-data-flow)
- [Repository layout](#repository-layout)
- [Requirements](#requirements)
- [Run locally](#run-locally)
- [Roles and permissions](#roles-and-permissions)
- [API overview](#api-overview)
- [Data and capability boundaries](#data-and-capability-boundaries)
- [Tests](#tests)
- [Deployment](#deployment)
- [Security notes](#security-notes)

## What the application does

RailPulse provides one interface for passengers and railway operations staff to inspect train state and request model-backed ETA predictions.

- **Passenger portal:** look up a train, inspect its stored state, request an ETA prediction, and view prediction history.
- **Staff portal:** use passenger train and prediction views, seed or refresh demo trains, submit isolated simulated state, and inspect network capability responses.
- **Admin portal:** use staff tools, clear demo data, and inspect backend, MongoDB, and ML model health.
- **Prediction display:** presents predicted arrival time, expected delay, an ETA uncertainty range, confidence, and model version when returned by the API.
- **Operational honesty:** features requiring unavailable live feeds are identified as unavailable rather than represented with fabricated data.

Authentication is shared across the portals. A portal is a user interface, not a security boundary; FastAPI validates tokens and enforces role access for protected operations.

## Architecture and data flow

```text
Browser (HTML + CSS + Vanilla JavaScript)
  -> FastAPI JSON API (Pydantic validation and authentication)
  -> ETA/delay feature pipeline and existing ML model
  -> MongoDB (live state, simulation state, users, prediction history)
  -> API response rendered by the browser
```

The frontend does not connect to MongoDB or load the model artifact. It calls the backend through a shared API client, sending bearer tokens after sign-in. The backend validates prediction input using the `TrainStateRequest` Pydantic schema, performs inference through the existing ML pipeline, saves prediction history, and returns the prediction response.

## Repository layout

```text
railpulse-github/
├── README.md                    # This repository-wide guide
├── railpulse-backend/           # FastAPI, schemas, MongoDB repositories, ML, tests
└── railpulse-frontend/          # Static HTML, CSS, and JavaScript application
```

## Requirements

- Python 3.10 or newer; local development has been run with Python 3.12.
- MongoDB running locally or an accessible MongoDB deployment.
- The trained model artifact at `railpulse-backend/models/railpulse_eta_model.pkl`. Model binaries are ignored by Git, so generate this file after cloning if it is absent (steps below).
- A modern browser. The frontend uses JavaScript ES modules and must be served over HTTP; opening `index.html` directly as a `file://` URL is not supported.

## Run locally

These instructions start the complete app from a fresh GitHub clone on Linux or macOS. Use three terminals and keep the MongoDB container, backend server, and frontend server running while you use the site. The example consistently uses `http://localhost:3000` for the frontend and `http://localhost:8000` for FastAPI.

### 0. Clone the repository

Replace the URL with this repository's GitHub clone URL:

```bash
git clone https://github.com/<YOUR_ACCOUNT>/<YOUR_REPOSITORY>.git
cd <YOUR_REPOSITORY>
```

Run the following commands from the repository root unless a step says otherwise.

### 1. Configure and start the backend

Install Python 3.10 or newer and Docker Desktop/Docker Engine. Start MongoDB in **Terminal 1**. For a new checkout, create a persistent local database container:

```bash
docker run -d --name railpulse-mongo -p 27017:27017 -v railpulse-mongo-data:/data/db mongo:7
```

If Docker says the container name already exists, start that existing container instead:

```bash
docker start railpulse-mongo
docker ps --filter name=railpulse-mongo
```

Alternatively, use a locally installed MongoDB service listening at `mongodb://localhost:27017`.

In **Terminal 2**, install the backend dependencies and configure the local environment:

```bash
cd railpulse-backend
python3 -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

Open `railpulse-backend/.env` and set private local admin/staff passwords and a JWT secret. Ensure the CORS origin matches the exact frontend URL below:

```dotenv
CORS_ORIGINS=http://localhost:3000
MONGODB_URI=mongodb://localhost:27017
ADMIN_USERNAME=admin
ADMIN_PASSWORD=<choose-a-local-admin-password>
STAFF_USERNAME=staff
STAFF_PASSWORD=<choose-a-local-staff-password>
JWT_SECRET_KEY=<random-secret-at-least-32-characters>
```

The model `.pkl` file is not tracked by Git. If it is missing, generate it from the included training CSV before starting the app:

```bash
python training/train.py
```

Start FastAPI **from the `railpulse-backend` directory** so Python can import the `app` package:

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Wait for `Application startup complete`. The health endpoint should return `"status":"ok"`, `"mongodb":"ok"`, and `"model":"ok"` at `http://localhost:8000/api/v1/health/`. Interactive API documentation is at `http://localhost:8000/docs`; the OpenAPI schema is at `http://localhost:8000/openapi.json`.

### 2. Start the frontend

In **Terminal 3**, start the static frontend server:

```bash
cd railpulse-frontend
python3 -m http.server 3000 --bind 127.0.0.1
```

Open **http://localhost:3000** so the browser origin matches CORS. The default frontend API URL is `http://localhost:8000/api/v1`; no frontend configuration change is needed. For a different URL, see [Frontend setup](railpulse-frontend/FRONTEND_SETUP.md) and update `CORS_ORIGINS` to the exact frontend origin.

### 3. Sign in and load demo trains

The backend seeds the admin and staff accounts from `railpulse-backend/.env` at startup. Sign in to the matching portal with those usernames and passwords. Do not publish the passwords. Passengers can register through the passenger portal.

From the staff or admin dashboard, use the demo environment controls to seed or refresh demo train state. Admins can also clear demo records. Once train state is available, select a train to inspect it and request an ETA prediction.

To stop the services, press `Ctrl+C` in the frontend and backend terminals. Stop MongoDB when finished:

```bash
docker stop railpulse-mongo
```

The named Docker volume preserves database data between container stops.

### Troubleshooting local startup

- **MongoDB connection refused or `ServerSelectionTimeoutError`:** start the existing container with `docker start railpulse-mongo`; verify it with `docker ps --filter name=railpulse-mongo`.
- **Docker says the name is already in use:** the container already exists; use `docker start railpulse-mongo`, not another `docker run` with that name.
- **`ModuleNotFoundError: No module named 'app'`:** change into `railpulse-backend`, activate its `.venv`, and run Uvicorn there, not from the repository root.
- **Frontend says `FastAPI offline`:** open `http://localhost:8000/api/v1/health/`. If healthy, open the frontend at `http://localhost:3000`, ensure `CORS_ORIGINS=http://localhost:3000`, and restart FastAPI after editing `.env`.
- **Browser reports a CORS error:** CORS must match the frontend origin exactly, including hostname and port. `localhost` and `127.0.0.1` are different origins.
- **Model unavailable:** verify `railpulse-backend/models/railpulse_eta_model.pkl` exists. If missing, activate the backend virtual environment and run `python training/train.py` from `railpulse-backend`.
- **Port already in use:** stop the process using it, or choose another port and update both `CORS_ORIGINS` and the URL opened in the browser.

## Roles and permissions

| Role | Main capabilities |
| --- | --- |
| Passenger | Register/sign in, view train state, request ETA predictions, and view prediction history. Cannot update live state or submit staff simulation. |
| Staff | Passenger capabilities, seed/refresh demo trains, submit simulation state, and access staff network capability views. Cannot clear demo data. |
| Admin | Staff capabilities, clear demo data, and inspect system health. |

FastAPI is authoritative for authorization. UI role checks improve navigation but do not replace backend permission checks.

## API overview

All endpoints use the `/api/v1` prefix.

- **Authentication:** `/auth/register`, `/auth/login`, `/auth/me`
- **Health and model readiness:** `/health/`
- **Train state and prediction history:** `/trains`, `/trains/{train_number}/state`, `/trains/{train_number}/predictions`
- **ETA prediction:** `POST /predict/eta`
- **Demo data:** `/demo/seed`, `/demo/refresh`, `/demo/reset`
- **Simulation:** `POST /simulation/update`
- **Network intelligence:** `/network/trains/{train_number}/delay-propagation`, `/network/trains/{train_number}/operational-risk`
- **Alerts and capability catalog:** `/alerts`, `/docs/capabilities`

See the backend README and `/docs` for request/response schemas and the complete API specification.

## Data and capability boundaries

The historical CSV and seeded demo records support train-level state and ETA/delay prediction. They do not constitute a live railway telemetry feed. Station sequence predictions, network delay propagation, operational risk, and automatic alert generation need additional real source data; the backend reports those limitations explicitly. Simulation state is stored separately from live train state and does not silently become live state.

Demo data is for development and demonstration. It must not be presented as authoritative real-time railway information.

## Tests

Run backend tests from the backend directory with its virtual environment active:

```bash
cd railpulse-backend
source .venv/bin/activate
pytest tests/
```

Some tests use fake database adapters. A running MongoDB is needed for operations that explicitly exercise the live database.

## Deployment

Pushing this repository to GitHub stores and versions the source code; it does not run the FastAPI service. GitHub Pages can host the static frontend, but it cannot run this Python API or MongoDB. Deploy the backend to a Python-capable hosting service and use a managed MongoDB database, then host the frontend on a static hosting service.

For production deployment:

1. Configure backend environment variables on the backend host: `MONGODB_URI`, `MONGODB_DB`, `MODEL_PATH`, `ENVIRONMENT=production`, `JWT_SECRET_KEY`, `ADMIN_PASSWORD`, `STAFF_PASSWORD`, and `CORS_ORIGINS`.
2. Use a strong random JWT secret (at least 32 characters), replace development credentials, and allow only the deployed frontend origin in `CORS_ORIGINS`.
3. Set `window.RAILPULSE_API_BASE_URL` to the deployed API base URL ending in `/api/v1` before the frontend module script runs.
4. Confirm `/health/` reports the API, MongoDB, and model as healthy before using predictions.

Never commit `.env` files, production credentials, database connection strings, or private keys. The repository ignores local environment files; hosting secrets belong in the provider's secret/environment settings.

## Security notes

- JWT and account settings are configured by the backend; production must not use development defaults.
- Keep MongoDB accessible only to the backend and configure authentication/network restrictions on hosted MongoDB.
- Use HTTPS for deployed frontend and API traffic.
- Configure exact frontend origins in production CORS; do not use a broad wildcard for authenticated application traffic.
- Demo train data is illustrative and should be clearly distinguished from live operational data.
