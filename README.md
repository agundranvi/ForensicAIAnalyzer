# CICC Forensic AI Analyzer

Local forensic investigation workspace using FastAPI, SQLite and the installed Ollama `cicc-agent:latest`. Source evidence, normalized artifacts, AI interpretations and investigator notes are stored separately. This is an initial standalone implementation, not a certified forensic suite. Validate representative exports before operational use.

## Start on Windows

From PowerShell:

```powershell
Set-Location D:\GitHub-Projects\projectForensicAIAnalyzer
# Dependencies are already installed in this workspace. On a fresh installation:
py -3.11 -m venv .venv
New-Item -ItemType Directory -Force .tmp | Out-Null
$env:TEMP = Join-Path $PWD '.tmp'
$env:TMP = $env:TEMP
.\.venv\Scripts\python -m pip install --no-cache-dir -r requirements-lock.txt
# Choose a username; password is prompted without echo (minimum 12 characters).
.\.venv\Scripts\python -m scripts.create_user admin --role admin
.\START-CFAA.ps1
```

Open http://127.0.0.1:8000. Stop with **Ctrl+C** in the server terminal. Alternatively double-click `START-CFAA.bat`. If port 8000 is occupied, use `.\START-CFAA.ps1 -Port 8001` and open http://127.0.0.1:8001. Start the existing Ollama app first. Startup verifies the model and migrates the database; it never downloads models. If a script execution policy blocks the PowerShell launcher, use the direct commands in [Installation](docs/INSTALLATION.md) rather than changing system policy.

## Workflow

1. Sign in and create a case with a unique reference.
2. Import a CSV/XLSX/JSON/XML export; inspect import summary and original fields.
3. Verify source hashes. Search artifacts and select source references for reports.
4. Inspect communication categories, financial indicators, endpoint graph and timeline.
5. Ask the local AI evidence-specific questions. Review every interpretation independently.
6. Write investigator findings, save a report draft, review and approve it, then export DOCX/PDF.

## Test

```powershell
$env:TEMP = Join-Path $PWD '.tmp'
$env:TMP = $env:TEMP
.\.venv\Scripts\python -m pytest -q
# Separate live local model test (synthetic data only; can take several minutes):
.\.venv\Scripts\python -m scripts.test_local_ai
```

Tests use isolated temporary databases and synthetic identifiers. The original prototype is retained at `docs/original-prototype.py`; the root `main.py` now exposes the authenticated app. Do not run the old prototype against evidence.

## Documentation

- [Installation](docs/INSTALLATION.md)
- [User manual](docs/USER_MANUAL.md)
- [Administrator guide](docs/ADMINISTRATOR.md)
- [Export compatibility](docs/COMPATIBILITY.md)
- [AI configuration](docs/AI_CONFIGURATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Security and evidence handling](docs/SECURITY.md)
- [Development status and limitations](DEVELOPMENT_STATUS.md)

No changes have been committed or pushed. Runtime data, reports, logs and secrets are excluded from Git.
