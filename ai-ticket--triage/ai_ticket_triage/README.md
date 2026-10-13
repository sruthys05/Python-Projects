# AI Ticket Triage

A small FastAPI service that stores support tickets and assigns a category and priority. It uses a trained scikit-learn model when available and a deterministic keyword classifier otherwise.

## Setup

From this directory, create and activate a virtual environment, then install dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Run

```powershell
uvicorn app.main:app --reload
```

The API is available at `http://127.0.0.1:8000`. Interactive API documentation is at `/docs`; `GET /health` checks service availability.

## API

- `POST /tickets` with `{"title": "...", "description": "..."}` creates and classifies a ticket.
- `GET /tickets` lists tickets. Optional `limit` (1-500) and `offset` query parameters support pagination.
- `GET /tickets/{ticket_id}` retrieves one ticket.

SQLite is used by default and the database file is created at `data/tickets.db`. Settings can be changed through `.env` or environment variables: `APP_NAME`, `DATABASE_URL`, and `MODEL_PATH`.

## Train the classifier

The sample CSV has `text` and `category` columns. Train a model from the project directory with:

```powershell
python -m app.ml.train
```

The generated model is saved under `app/ml/models/` and is excluded from version control. The sample data is illustrative; replace it with labeled tickets representative of your support domain before relying on model predictions.

## Tests

```powershell
pytest
```
