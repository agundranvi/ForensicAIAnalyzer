param([ValidateRange(1024,65535)][int]$Port = 8000)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $python)) { throw 'Missing environment. Run: py -3.11 -m venv .venv; .\.venv\Scripts\python -m pip install -r requirements.txt' }
& $python -c "import sys; assert sys.version_info >= (3,11); import fastapi, sqlalchemy, alembic, argon2, jinja2, defusedxml, docx, reportlab, PIL, multipart"
if ($LASTEXITCODE -ne 0) { throw 'Missing dependency or Python < 3.11. Install requirements.txt.' }
try { $models = Invoke-RestMethod 'http://127.0.0.1:11434/api/tags' -TimeoutSec 10 } catch { throw 'Ollama is unavailable. Start the existing Ollama application and retry.' }
if ('cicc-agent:latest' -notin $models.models.name) { throw 'Required existing model cicc-agent:latest is unavailable. No model will be downloaded.' }
& $python -m alembic upgrade head
if ($LASTEXITCODE -ne 0) { throw 'Database migration failed. Back up data and consult the administrator.' }
Write-Host "CFAA: http://127.0.0.1:$Port - press Ctrl+C to stop"
& $python -m uvicorn app.main:app --host 127.0.0.1 --port $Port --no-server-header

if ($LASTEXITCODE -ne 0) { throw "CFAA server stopped with exit code $LASTEXITCODE. Check whether port $Port is already occupied." }
