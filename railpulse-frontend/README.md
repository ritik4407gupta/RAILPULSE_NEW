# RailPulse Frontend

A framework-free, ES module frontend for the existing RailPulse FastAPI backend. It does not contain a backend, connect to MongoDB, run the ML artifact, or invent railway data.

## Run locally

From this directory, start any static server:

```bash
python3 -m http.server 3000
```

Then open `http://localhost:3000`. The default API base is `http://localhost:8000/api/v1`.

For another API origin, define `window.RAILPULSE_API_BASE_URL` before `js/app.js` in `index.html`, or use the documented deployment configuration in `FRONTEND_SETUP.md`.

## Supported routes

The UI maps to passenger, staff, and admin role portals. It uses the verified API routes for authentication, train state, ETA prediction, history, simulation, health, alerts, capability catalog, propagation, and operational risk. Unsupported user management and map/location features are intentionally absent because the backend does not expose those contracts.