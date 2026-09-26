# RailPulse Backend Explanation

## 1. Purpose

RailPulse is a FastAPI backend for dynamic railway ETA and delay intelligence. Its immediate job is to receive a train's current operating state, estimate when the train will arrive, estimate the expected delay, classify the delay, and preserve the prediction and train state for later use.

The backend is also the foundation for the larger SIH26028 vision: moving railway information from static timetable reporting toward continuously updated prediction, explanation, warning, and decision support.

The current implementation deliberately does not invent station-level or network-level data that is absent from the supplied dataset. It exposes those future capabilities through explicit API contracts and returns `future_data_required` until real route schedules, station sequences, live locations, and operational events are connected.

## 2. Problem Being Solved

Static railway schedules answer what was planned, but they do not reliably answer what is happening now. A train can be late because of slow running, a late departure, congestion, or other operational conditions.

RailPulse addresses the first and currently supported part of this problem:

- Accept current train state through an API.
- Convert the state into the exact feature contract used during ML training.
- Predict remaining travel time and delay.
- Convert remaining travel time into an absolute ETA.
- Return an ETA range and calibrated confidence information.
- Classify the delay as `ON_TIME`, `MINOR`, `MODERATE`, `MAJOR`, or `SEVERE`.
- Store the prediction and input snapshot in MongoDB.
- Store the latest live train state for dashboards and later requests.
- Provide historical predictions for comparison and monitoring.

This gives passengers and railway staff a consistent operational prediction API instead of relying only on a static scheduled arrival.

## 3. High-Level Architecture

```text
Client / dashboard / railway feed
                |
                v
        FastAPI API layer
   authentication, RBAC, validation
                |
                v
       Service and feature layer
   request normalization and orchestration
                |
                v
       ML inference layer
  ETA pipeline + delay pipeline + metadata
                |
       ------------------------
       |                      |
       v                      v
 MongoDB persistence      Prediction response
 live state, history,     ETA, delay, range,
 simulations, users       category, confidence
```

The code is organized into these layers:

### Application layer

`app/main.py` creates the FastAPI application, configures CORS, connects to MongoDB during startup, creates indexes, seeds staff/admin accounts, loads the ML artifact, and registers all routers.

### API layer

`app/api/routes/` contains endpoints for authentication, prediction, health, train state, simulation, network intelligence, alerts, and capability documentation.

### Schema layer

`app/schemas/` contains Pydantic request and response contracts. Pydantic rejects malformed requests before they reach database or ML code.

### Service layer

`app/services/` coordinates ETA calculation, feature construction, and explicit future-data capability responses.

### ML layer

`app/ml/` contains the shared feature contract, model loader, prediction code, delay classification, and model metadata access.

### Database layer

`app/db/` contains the asynchronous Motor connection and repositories for users, predictions, live train state, simulations, and alerts.

## 4. Startup Flow

When Uvicorn starts the application:

1. FastAPI creates the application and registers routes.
2. CORS is configured from `CORS_ORIGINS`.
3. MongoDB is connected with bounded connection and socket timeouts.
4. MongoDB is pinged so startup does not claim a database connection that is unavailable.
5. Required MongoDB indexes are created.
6. Default staff and admin accounts are inserted only if they do not already exist.
7. `models/railpulse_eta_model.pkl` is loaded.
8. The loader validates that the artifact contains both pipelines, the expected feature list, metadata, and the configured model version.
9. The application begins serving requests.

If MongoDB is unavailable, the application currently fails startup. This is intentional for normal deployment because prediction and authentication persistence require MongoDB. The health endpoint separately reports database and model status after startup.

## 5. Authentication and RBAC

RailPulse uses JWT bearer authentication and Argon2 password hashing.

### Roles

- `PASSENGER`: can register, log in, view train state, view prediction history, request ETA predictions, and query supported passenger-facing APIs.
- `STAFF`: has passenger permissions plus live-state ingestion, simulation, delay-propagation architecture, and operational-risk architecture access.
- `ADMIN`: has staff permissions and is intended for system administration and monitoring extensions.

### Authentication flow

1. A passenger registers with `POST /api/v1/auth/register`.
2. The password is hashed with Argon2 before it is stored.
3. The user logs in with `POST /api/v1/auth/login`.
4. The backend returns a signed JWT containing the username, role, and expiration time.
5. Protected routes read the `Authorization: Bearer <token>` header.
6. The token is decoded and the user is loaded from MongoDB.
7. Role dependencies enforce permissions before route execution.

Production configuration rejects the development JWT secret and default seed passwords. JWT expiration is configured by `ACCESS_TOKEN_EXPIRE_MINUTES`.

## 6. What the ML Model Predicts

The saved artifact is `models/railpulse_eta_model.pkl`, version `eta-v2`. It contains two scikit-learn pipelines:

1. An ETA regressor that predicts remaining travel time in minutes.
2. A delay regressor that predicts delay in minutes.

Both pipelines use preprocessing and an `XGBRegressor` model.

### Model features

The shared feature contract is defined in `app/ml/features.py` and is used by both training and inference:

Numeric features:

- `distance_remaining_km`
- `scheduled_travel_time_minutes`
- `scheduled_arrival_hour`
- `scheduled_arrival_minute`
- `departure_year`
- `departure_month`
- `departure_day_of_week`

Categorical features:

- `train_number`
- `train_type`
- `source`
- `destination`
- `season`
- `run_frequency`

The feature list is stored in the model metadata. The loader refuses an artifact whose feature metadata does not exactly match the inference contract.

### Prediction calculation

For a request with current timestamp `T` and predicted remaining minutes `R`:

```text
predicted_eta = T + R minutes
```

The delay regressor output is classified as:

- `ON_TIME`: delay <= 5 minutes
- `MINOR`: delay <= 15 minutes
- `MODERATE`: delay <= 60 minutes
- `MAJOR`: delay <= 120 minutes
- `SEVERE`: delay > 120 minutes

The model rejects non-finite outputs and clamps negative predicted time or delay to zero because negative travel time and negative delay are not meaningful API results.

### ETA uncertainty

Confidence is not hardcoded. During training, the validation-set absolute errors are used to calculate an error interval at the configured calibration level. The saved metadata contains:

- Calibration level: `0.90`
- ETA interval: approximately `97.16` minutes for the current artifact
- Measured ETA calibration coverage: `0.95`
- Delay interval: approximately `102.84` minutes
- Measured delay calibration coverage: `0.95`

The API uses the calibrated ETA interval around the predicted ETA and returns the measured validation coverage as the confidence value. This is more defensible than claiming a fixed confidence for every request, although the interval is still limited by the small and sparse dataset.

## 7. ML Training and Evaluation

`training/train.py` loads the 100-row historical CSV and creates one observed trip row per source record. It does not generate synthetic progress checkpoints and does not use final delay as a current-delay input feature.

The dataset is split chronologically and by trip group:

- Training: 59 rows
- Validation: 20 rows
- Test: 21 rows

The groups are disjoint, and later dates are held out from earlier dates. This better represents future prediction than a random row split.

The training pipeline evaluates both ML predictions and simple baselines. On the current chronological test set:

| Target | Baseline MAE | ML MAE | Baseline RMSE | ML RMSE |
| --- | ---: | ---: | ---: | ---: |
| ETA | 25.46 min | 35.67 min | 41.13 min | 46.86 min |
| Delay | 25.46 min | 33.73 min | 41.13 min | 44.10 min |

The ML model currently underperforms the baseline because the available dataset is small and lacks live sectional, speed, station, congestion, and operational observations. These metrics are stored in the artifact metadata and are exposed through the health endpoint. They should be treated as an honest prototype evaluation, not as proof of production accuracy.

## 8. Main Prediction Flow

The normal ETA request flow is:

1. A client sends `POST /api/v1/predict/eta` with a `TrainStateRequest`.
2. The authentication dependency validates the JWT.
3. Pydantic validates the request fields.
4. `feature_service.py` calls the shared inference feature builder.
5. The feature builder creates the same ordered feature set used during training.
6. The ETA and delay pipelines run inference.
7. The service calculates absolute ETA, ETA bounds, delay category, confidence, and model version.
8. A prediction document is inserted into MongoDB.
9. The request state is upserted into `live_train_state`.
10. The response is returned to the caller.

This means every prediction has both an answer and an input snapshot that can later be used for history, debugging, evaluation, and future model monitoring.

## 9. Current API Endpoints

All routes use the `/api/v1` prefix. FastAPI also provides interactive documentation at `/docs` and the OpenAPI schema at `/openapi.json`.

### Authentication

- `POST /api/v1/auth/register`
  - Registers a passenger account.
  - Public endpoint.

- `POST /api/v1/auth/login`
  - Validates credentials and returns a JWT.
  - Public endpoint.

- `GET /api/v1/auth/me`
  - Returns the authenticated user's username, role, and name.

### Health and documentation

- `GET /api/v1/health/`
  - Pings MongoDB.
  - Checks model artifact existence and validity.
  - Returns model version, feature metadata, evaluation metrics, and uncertainty metadata.

- `GET /api/v1/docs/capabilities`
  - Lists capabilities that are available now and capabilities that require future live data.

### Prediction

- `POST /api/v1/predict/eta`
  - Predicts remaining time, ETA, delay, delay category, ETA range, confidence, and model version.
  - Persists both the prediction and the current input state.

### Live train state and history

- `GET /api/v1/trains/{train_number}/state`
  - Returns the latest state stored in `live_train_state`.

- `PUT /api/v1/trains/{train_number}/state`
  - Staff/admin-only ingestion endpoint for a future real operational feed.
  - Updates live state without requiring a prediction call.

- `GET /api/v1/trains/{train_number}/predictions/latest`
  - Returns the most recent prediction for a train.

- `GET /api/v1/trains/{train_number}/predictions?limit=20&skip=0`
  - Returns paginated prediction history and total count.

### Simulation

- `POST /api/v1/simulation/update`
  - Staff/admin-only simulated state update.
  - Stores data in `simulation_states`.
  - Does not overwrite `live_train_state`, keeping hypothetical scenarios separate from real state.

### SIH26028 capability architecture

- `GET /api/v1/trains/{train_number}/upcoming-stations`
  - Defines the station-wise ETA response contract.
  - Currently returns `future_data_required` because the dataset has no station sequence or station observations.

- `GET /api/v1/network/trains/{train_number}/delay-propagation`
  - Staff/admin-only contract for downstream train and section impact.
  - Currently returns no affected trains because network topology and live interactions are unavailable.

- `GET /api/v1/network/trains/{train_number}/operational-risk`
  - Staff/admin-only contract for congestion and operational risks.
  - Currently returns no risks because occupancy, junction, platform, and signal events are unavailable.

- `GET /api/v1/alerts`
  - Reads stored alerts from MongoDB.
  - If no alerts exist, returns `future_data_required` rather than inventing warnings.

## 10. MongoDB Collections

### `users`

Stores usernames, Argon2 password hashes, roles, and optional names. The username is unique.

### `predictions`

Stores:

- train number
- prediction timestamp
- model version
- input snapshot
- predicted ETA
- predicted remaining minutes
- predicted delay minutes
- delay category

The compound index `(train_number, timestamp descending)` supports latest-prediction and history queries.

### `live_train_state`

Stores the latest operational state for each train. The train number is unique and the record identifies the state as live.

### `simulation_states`

Stores staff/admin hypothetical updates independently from live state. This separation prevents a what-if scenario from appearing as real operational information.

### `alerts`

Stores alert records when a future alert-generation source is connected. Indexes support train/time lookup and acknowledgement filtering.

Indexes are created during application startup.

## 11. What the Backend Solves Today

With the available historical data, RailPulse can:

1. Authenticate users and enforce passenger/staff/admin permissions.
2. Accept a train state through a stable API contract.
3. Predict final remaining travel time and delay.
4. Return an absolute ETA with a measured uncertainty interval.
5. Classify the predicted delay.
6. Preserve live state and prediction history.
7. Support staff/admin simulation without corrupting live state.
8. Expose model health, evaluation metrics, and API documentation.
9. Provide extension points for station-wise and network-level intelligence.

This changes the basic user experience from “the schedule says the train arrives at X” to “given the current state, the model estimates arrival at Y, with expected delay Z and an uncertainty range.”

## 12. What Requires Future Data

The current CSV has train-level historical arrival and delay records. It does not contain:

- ordered upcoming stations
- GPS or current train positions
- section entry and exit times
- current speed histories
- track occupancy
- signal or platform status
- junction conflicts
- weather or maintenance events
- connections and passenger journeys
- other trains' live state

Therefore the following SIH26028 capabilities are architecture-ready but not currently calculated:

- ETA at every upcoming station
- delay propagation to other trains
- congestion and operational-risk scoring
- early-warning generation from live events
- digital railway twin state
- connection-risk calculation
- missed-train recovery and alternative train recommendation
- operational what-if comparison involving real network conflicts

The API marks these responses with `status: "future_data_required"` and returns empty result arrays. This keeps the contract ready for future integration while preserving data integrity today.

## 13. How It Solves the Larger SIH26028 Problem

The intended RailPulse progression is:

```text
Live train feed
      |
      v
Validated current state
      |
      v
ETA and delay prediction
      |
      v
Prediction history and confidence
      |
      v
Explanation, warnings, and propagation
      |
      v
Passenger and railway-staff decisions
```

The current backend implements the validated-state, prediction, confidence, history, authentication, and persistence layers. Its schemas, routes, repositories, indexes, and explicit capability statuses provide the integration boundaries for the future station, network, and passenger-intelligence layers.

## 14. One-Minute Explanation

> RailPulse is a FastAPI railway intelligence backend. An authenticated client sends the current state of a train, including its route, distance, schedule, and operating context. A leakage-aware XGBoost pipeline predicts how many minutes remain and how much delay is expected. The backend converts that result into an ETA, delay category, confidence range, and model version, then stores the prediction and live train state in MongoDB. Staff can ingest live state and run isolated simulations, while prediction history and health endpoints support dashboards and monitoring. Station-wise ETA, delay propagation, operational risk, and alert generation are exposed as structured extension points, but they are clearly marked as requiring live railway data that the current CSV does not provide.

## 15. Important Scope Note

RailPulse backend is an API, ML, authentication, and persistence service. It is not the frontend dashboard itself. A frontend can consume these endpoints to display ETA cards, train state, prediction history, health information, staff simulation results, and future network-intelligence views.
