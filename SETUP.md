# Setup

Use Python 3.12 (tested) and Node.js 22.12+ or 24 (tested). Other Python versions may depend on binary-wheel availability. Synthetic data only. Keep the API local.

## Linux / macOS — backend terminal

From the repository root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Using `python -m uvicorn` ensures the activated environment is used, not `/usr/bin/uvicorn`. If `pymupdf` is missing, rerun the requirements installation in this environment.

## Windows PowerShell — backend terminal

```powershell
cd backend
py -3.12 -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

## Frontend — separate terminal

From the repository root:

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5173 --strictPort
```

Open http://127.0.0.1:5173. API documentation: http://127.0.0.1:8000/docs. Stop each server with Ctrl+C in its terminal.

The backend database defaults to `backend/doctrace.db` when started from `backend`. Downloadable copies are in `backend/stamped`. These are local generated data and excluded from Git. Back them up together before changing computers. No remote synchronization is configured.

Optional environment settings: `DOCTRACE_DB`, `DOCTRACE_OUTPUT_DIR`, `DOCTRACE_CORS_ORIGINS` (comma-separated frontend origins), and frontend `VITE_API_BASE` (default `http://127.0.0.1:8000/api`). Restart servers after changing settings. Never expose this unauthenticated prototype publicly.

## Pulling the corrected code

Stop the servers, run `git status` and preserve any local edits, then run `git pull --ff-only` from the repository root. Reinstall backend requirements and run `npm ci` in frontend. Do not reset or delete your local database.
