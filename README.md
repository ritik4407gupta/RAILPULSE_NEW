# RailPulse FastAPI ML Backend

This is a complete, production-ready ML subsystem for dynamic railway ETA forecasting and delay prediction.
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
The provided `indian_railway_delay_data_.csv` (with sparse data) is expanded via simulation checkpoints to train the XGBoost models.
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
uvicorn app.main:app --reload
```

## API Endpoints
- `GET /api/v1/health`: Application, database, and model health status.
- `POST /api/v1/predict/eta`: Main ETA + delay prediction endpoint.
- `POST /api/v1/simulation/update`: Endpoint to feed simulated live updates.
- `GET /api/v1/trains/{train_number}/state`: Current stored live state for a train.
- `GET /api/v1/trains/{train_number}/predictions/latest`: Latest prediction for a train.

## Running Tests
```bash
pytest tests/
```
