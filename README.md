# Spotify Dashboard Backend

This is the backend API server for the Spotify Dashboard project. It is built using FastAPI and handles data upload, processing, and serving aggregated metrics for the frontend dashboard.

***

## Folder Structure

```
SPOTIFY_DASHBOARD_BACKEND
├── app
│   ├── __init__.py
│   ├── main.py                # FastAPI app entry point
│   ├── routes
│   │   ├── __init__.py
│   │   ├── metrics.py         # API endpoints for metrics
│   │   └── upload.py          # API endpoints for uploading data
│   └── services
│       ├── __init__.py
│       └── preprocessing.py   # Data loading and preprocessing logic
├── requirements.txt           # Python dependencies
├── README.md                  # This file
└── test_spotify_frontend.html # (Optional) simple frontend test file
```


***

## Setup Instructions

### Prerequisites

- Python 3.13 installed
- Recommended: Create and activate a virtual environment to isolate dependencies


### Installation

1. Clone the repository:
```bash
git clone 
cd SPOTIFY_DASHBOARD_BACKEND
```

2. Create and activate virtual environment (Unix/macOS):
```bash
python3 -m venv .venv
source .venv/bin/activate
```

(Windows PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```


***

## Running the Backend Server

Run the FastAPI server with `uvicorn` (already included in requirements):

```bash
uvicorn app.main:app --reload
```

- The API will be available at http://localhost:8000
- The `--reload` flag restarts server upon code changes (development convenience)

***

## API Endpoints

### Upload Routes

- POST `/upload/` : Upload Spotify JSON files for processing. Accepts multiple files + date range.
- Stores preprocessed data in memory with unique dataset IDs.


### Metrics Routes

- GET `/metrics/{dataset_id}` : Fetch aggregated metrics for dataset within optional date range.
- Provides JSON of listening behavior, time-based stats, platform breakdown, session info, and more.

***

## Development Notes

- Data preprocessing is in `app/services/preprocessing.py`
- API routes are defined in `app/routes/upload.py` and `app/routes/metrics.py`
- In-memory dataset storage (simple dict) for prototyping; consider DB for production.
- Test frontend is available as `test_spotify_frontend.html` for basic checks.

***

## Extending the Backend

- Add persistent storage support (e.g., PostgreSQL, Redis)
- Implement authentication for upload endpoints
- Expand metrics with additional Spotify data fields or visualizations

***

## License

MIT License
***

If you have any questions or want to contribute, feel free to open issues or pull requests!

***