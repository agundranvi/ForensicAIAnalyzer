# Troubleshooting

- Missing dependency: use the virtual environment interpreter and `python -m pip install --no-cache-dir -r requirements-lock.txt`. If pip stalls creating cache/temp files, point TEMP and TMP at the project .tmp directory as in README.
- Model unavailable: start the existing Ollama app, then run `Invoke-RestMethod http://127.0.0.1:11434/api/tags`. Confirm cicc-agent:latest is present; do not download or replace it without authorization.
- Port in use: close your own previous server using Ctrl+C. Do not terminate unrelated processes. For testing use `python -m uvicorn app.main:app --host 127.0.0.1 --port 8001`. Login origin protection follows the incoming localhost host/port.
- Login required/CSRF rejected: reload the page and sign in again. Session expires after eight hours. Ten failed logins per host within five minutes temporarily throttle login attempts.
- Unsupported/failed import: inspect import summary. Preserve the original and use the compatibility guide. Cancel a failed/interrupted record before retrying identical bytes. Completed duplicates are rejected.
- Interrupted import after crash: restart, inspect its interrupted status, cancel and retry. Artifacts are committed atomically; incomplete batches should not appear.
- Empty timeline: records without explicit timezones do not have UTC timestamps. Check original values and time warnings, or broaden the search.
- AI insufficient/invalid: search directly, use a shorter specific question, and inspect source records. Never treat model failure as absence of evidence.
- PDF character limitations: the initial PDF renderer uses standard fonts. Non-Latin scripts may not render correctly; DOCX preserves Unicode. Inspect each generated report before use. DOCX visual rendering requires an available LibreOffice renderer and is not yet verified on this workstation.
- Logs: Uvicorn prints runtime failures to the local console; activity events are in the database audit table. Protect console logs, backups and exported reports.
