# Installation

Python 3.11 or newer is required. The existing workspace environment is Python 3.11.9. Use the commands in README for installation. Packages and frontend assets require Internet access during setup only; no evidence is transmitted. Frontend assets are vendored under static/vendor, including their upstream license headers. `python -m scripts.vendor_assets` refreshes the pinned frontend files; do not run it on an evidence workstation without change approval.

Create the first administrator with `python -m scripts.create_user admin --role admin`, using the virtual environment interpreter. Do not put passwords in command arguments, environment files or Git. Additional investigators use the same command without `--role admin`.

Manual startup (also works without PowerShell script execution):

```powershell
Set-Location D:\GitHub-Projects\projectForensicAIAnalyzer
.\.venv\Scripts\python -m alembic upgrade head
.\.venv\Scripts\python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --no-server-header
```

Manual startup does not check Ollama first. The UI and imports work without Ollama; AI requests return a generic service error when unavailable. Press Ctrl+C to stop. Do not expose Uvicorn on 0.0.0.0. For dependency validation run `python -m pip check` in the virtual environment. `requirements-lock.txt` records the verified environment.
