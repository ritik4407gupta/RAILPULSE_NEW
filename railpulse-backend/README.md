# RailPulse FastAPI ML Backend

This is a FastAPI ML subsystem for dynamic railway ETA forecasting and delay prediction.
It uses FastAPI + Pydantic as the backend application layer and MongoDB for persistence, matching the SIH26028 specifications.

## Architecture Highlights
- **Single Backend Framework**: Uses FastAPI to handle API contracts, validation, model inference, prediction history, and model status.
- **Strict Data Contracts**: Uses Pydantic v2 to validate train states, predict endpoints, and output payload.
- **Machine Learning**: Uses `XGBoost` for ETA and Delay prediction. Packaged completely with `scikit-learn`'s `Pipeline` to ensure preprocessing runs dynamically during inference.
- **Persistence**: Integrates `MongoDB` (via `motor`) for storing prediction logs, live train state, and features.

## Setup Instructions

### 1. Prerequisites
- Python 3.10+
- MongoDB instance running

### 2. Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Training the Model
The provided `indian_railway_delay_data_.csv` is sparse historical train-level data. The v2 pipeline uses leakage-free observed trip rows, chronological holdout evaluation, and saved uncertainty calibration.
```bash
python training/train.py
```
This will generate `models/railpulse_eta_model.pkl`.

### 4. Configure Environment
Copy `.env.example` to `.env` and adjust the MongoDB connection string.
```bash
cp .env.example .env
```

### 5. Run the Server
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## API Endpoints
- `GET /api/v1/health`: Application, database, and model health status.
- `GET /api/v1/docs/capabilities`: Capability catalog, including future-data requirements.
- `POST /api/v1/auth/register`: Passenger registration.
- `POST /api/v1/auth/login`: JWT login.
- `GET /api/v1/auth/me`: Authenticated user details.
- `POST /api/v1/predict/eta`: Main ETA + delay prediction endpoint.
- `POST /api/v1/simulation/update`: Endpoint to feed simulated live updates.
- `GET /api/v1/trains/{train_number}/state`: Current stored live state for a train.
- `GET /api/v1/trains/{train_number}/predictions/latest`: Latest prediction for a train.
- `GET /api/v1/trains/{train_number}/predictions`: Paginated prediction history.
- `PUT /api/v1/trains/{train_number}/state`: Staff/admin live-state ingestion.
- `GET /api/v1/trains/{train_number}/upcoming-stations`: Station ETA contract. Returns `future_data_required` until route/station feed data is connected.
- `GET /api/v1/network/trains/{train_number}/delay-propagation`: Delay propagation contract. Requires live network data.
- `GET /api/v1/network/trains/{train_number}/operational-risk`: Operational risk contract. Requires live network data.
- `GET /api/v1/alerts`: Stored alert query. Alert generation requires live events and rules.

FastAPI's interactive documentation is available at `/docs`; the OpenAPI schema is available at `/openapi.json`.

### Phase 3 data boundaries

The current CSV contains train-level historical arrival and delay observations. It does not contain station sequences, live positions, section occupancy, junction conflicts, or operational events. Accordingly, upcoming-station ETA, delay propagation, operational-risk analysis, and generated alerts return an explicit `future_data_required` status with empty result arrays instead of fabricated data.

Simulation writes are stored in the `simulation_states` collection and never overwrite `live_train_state`. The live-state ingestion endpoint is reserved for staff/admin callers and is ready for a future operational feed.

## Running Tests
```bash
pytest tests/
```

### Production configuration

Set `ENVIRONMENT=production`, provide a random `JWT_SECRET_KEY` of at least 32 characters, replace both seed passwords, and set `CORS_ORIGINS` to a comma-separated allowlist. The application uses Argon2 password hashing, expiring JWTs, role checks, bounded MongoDB connection timeouts, and validates the model feature contract at startup. No default development secrets are accepted in production.

The test suite uses fake database adapters for deterministic API tests. A live MongoDB integration run requires a MongoDB instance configured through `MONGODB_URI`; it is not silently treated as passed when unavailable.
