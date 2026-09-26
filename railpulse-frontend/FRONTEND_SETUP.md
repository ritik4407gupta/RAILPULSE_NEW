# Frontend setup

## 1. Start the frontend

```bash
cd railpulse-frontend
python3 -m http.server 3000
```

Open `http://localhost:3000`. A static server is required because the application uses ES modules.

## 2. Configure the FastAPI URL

The default is `http://localhost:8000/api/v1`. To override it, add this line immediately before the module script in `index.html`:

```html
<script>window.RAILPULSE_API_BASE_URL = 'https://api.example.com/api/v1';</script>
```

The backend must allow the frontend origin in `CORS_ORIGINS`, for example `http://localhost:3000`.

## 3. Start the backend

From `railpulse-backend`, install its Python requirements, ensure MongoDB is running, configure `.env`, and start:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The model artifact must exist at the configured `MODEL_PATH`. The browser never sees MongoDB credentials or the model file.

## 4. Authentication and roles

Passenger registration calls `POST /api/v1/auth/register`; the backend creates only a `PASSENGER` user. All portals call the same `POST /api/v1/auth/login` endpoint. The frontend checks the returned role for portal navigation, while FastAPI remains the security authority. Bearer tokens are kept in `sessionStorage` by default, or `localStorage` when the user selects remember session. Logout clears both.

## 5. API integration

The frontend uses these verified contracts:

- `GET /api/v1/health/`
- `GET /api/v1/docs/capabilities`
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `GET /api/v1/trains/{train_number}/state`
- `GET /api/v1/trains/{train_number}/predictions/latest`
- `GET /api/v1/trains/{train_number}/predictions`
- `PUT /api/v1/trains/{train_number}/state`
- `GET /api/v1/trains/{train_number}/upcoming-stations`
- `POST /api/v1/predict/eta`
- `POST /api/v1/simulation/update`
- `GET /api/v1/network/trains/{train_number}/delay-propagation`
- `GET /api/v1/network/trains/{train_number}/operational-risk`
- `GET /api/v1/alerts`

All calls use one API client with JSON parsing, bearer headers, timeout handling, normalized errors, and 401 session cleanup. The prediction form forwards the stored `TrainStateRequest` shape instead of creating a second frontend contract.

## 6. Honest capability boundaries

The backend currently returns `future_data_required` for upcoming station ETAs, propagation, operational risk, and generated alerts when source feeds are absent. The UI shows those typed limitations directly. There is no fake train list, map coordinate, aggregate metric, confidence, or alert.

## 7. Troubleshooting

- `FastAPI offline`: confirm Uvicorn is listening on port 8000 and the configured URL is correct.
- CORS error: add the exact frontend origin to `CORS_ORIGINS` and restart FastAPI.
- `401`: sign in again; the client clears an expired or invalid session.
- `403`: the account role cannot call that backend route.
- `404` train state: the backend has no stored live state for that number. Staff simulation is separate and does not make it live.
- Prediction unavailable: confirm MongoDB and the model are healthy, then inspect `/docs` and `/openapi.json`.

## 8. Production notes

Serve this directory from a static host over HTTPS, set an explicit API origin at build/deploy time, and configure a narrow production CORS allowlist. Do not place JWT secrets, MongoDB URIs, seed credentials, or model paths in this frontend.