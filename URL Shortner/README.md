# URL Shortener

A small FastAPI service for creating expiring short links, redirecting visitors, and viewing click statistics. URL records are stored with SQLAlchemy; redirects use a custom O(1) LRU cache implemented with a hash map and doubly linked list.

## Setup

Use Python 3.10 or newer. From this directory, create and activate a virtual environment, then install the dependencies:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The included `.env` provides the defaults and is loaded automatically. Environment variables set in the shell take precedence.

| Variable | Default | Description |
| --- | --- | --- |
| `DATABASE_URL` | `sqlite:///./data/urls.db` | SQLAlchemy connection URL. PostgreSQL URLs are supported with the included psycopg driver. |
| `CACHE_SIZE` | `256` | Maximum number of redirect entries held in memory. |
| `DEFAULT_EXPIRY_DAYS` | `30` | Link lifetime when no expiry is specified. |
| `SHORT_CODE_LENGTH` | `7` | Length of generated base62 codes. |
| `MAX_URL_LENGTH` | `2048` | Maximum accepted destination URL length. |

## Run

```powershell
uvicorn app.main:app --reload
```

Open `http://127.0.0.1:8000/docs` for the interactive API documentation. The SQLite database and parent directory are created automatically on first run.

## API

### `POST /shorten`

Request:

```json
{
  "url": "https://example.com/a-page",
  "expires_in_days": 14
}
```

`expires_in_days` is optional; the configured default is used when omitted. The response includes the generated `short_code`, full `short_url`, original URL, and creation/expiration timestamps. Destinations must use HTTP or HTTPS.

### `GET /{short_code}`

Returns a temporary redirect (307) to the destination and increments its click count. Missing codes return 404; expired links return 410.

### `GET /stats/{short_code}`

Returns the original URL, timestamps, and click count. Missing codes return 404; expired links return 410.

## Tests

```powershell
python -m pytest -q
```

Tests use temporary in-memory SQLite databases and do not write link records to the configured development database.

## LRU design

The cache keeps a dictionary from keys to nodes and a doubly linked list ordered from most recently used to least recently used. Reads and updates move a node to the front; inserting beyond capacity removes the tail node. Dictionary lookup and linked-list updates are O(1), with O(cache size) memory. Cached entries carry their expiry time, and each redirect still updates the persistent click counter.
