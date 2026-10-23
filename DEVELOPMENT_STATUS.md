# Development status

Updated 23 October 2026 (Asia/Singapore).

A working standalone local implementation is present. It is ready for synthetic-data evaluation; the full operational definition of done is not claimed because real vendor fixtures and browser/DOCX visual verification remain unavailable.

## Implemented milestones

| Milestone | Result |
| --- | --- |
| Foundation | Python 3.11.9 verified; FastAPI/Jinja2 application; SQLAlchemy schema; three additive Alembic revisions; Argon2 authentication; server sessions; admin/investigator roles; case authorization; local dashboard and theme. |
| Evidence import | CSV/XLSX/JSON/XML generic adapters; original byte retention; SHA-256 inventory and verification; original fields; record references; timestamp uncertainty; duplicate detection; atomic batches; cancellation at record boundaries; failed/interrupted recovery; indexed search and pagination. |
| Local AI | Existing cicc-agent:latest verified and unchanged; SQLite FTS5 retrieval; bounded evidence prompts; structured JSON schema; exact-excerpt/source checks; explicit insufficiency; successful and failed query history. Loopback client ignores proxies and refuses redirects. |
| Investigation tools | Direction/message/call counts; frequency chart; endpoint counts; text/contact/application/category/direction/date filters; indicator extraction and audited JSON export; communication graph with evidence drill-down; connected endpoint clusters; timeline and uncertain-time listing. |
| Reporting | Editable findings before approval; saved case/inventory/AI-history snapshot; selected evidence; fifteen report sections; source tables and hashes; category chart; DOCX/PDF export gated by approval and authorization. PDF visually inspected on all two pages of a synthetic report. |
| Security/deployment/docs | CSRF; bounded request/upload sizes; XML entity protection; archive traversal/expansion checks; generic production errors; case-scoped audit; local-only binding/assets; startup scripts; synthetic fixture; installation, user, administrator, compatibility, AI, troubleshooting and evidence-handling guides. |

Original main.py is preserved at docs/original-prototype.py. The root entry point now imports the authenticated application. Git was initialized because no repository existed. No commit or push was performed. No real evidence was used. No model was downloaded, replaced or reconfigured.

## Verification evidence

- `python -m pytest -q`: **17 passed**, one upstream Starlette warning about httpx test-client deprecation. Tests cover all four formats, source bytes/hashes, duplicates, search, provenance, roles/case isolation, CSRF, login/logout/expiry, request limits, multipart spooling, malicious XML/archive inputs, cancellation, retry, tamper detection, mocked prompt injection/citation rejection, failed AI history, FTS isolation, report selection/approval/snapshots, PDF/DOCX generation, local assets and a 5,000-record import.
- Synthetic 5,000-record import measured **1.284 seconds** in the recorded performance run (workstation-specific, not a throughput guarantee).
- `python -m scripts.test_local_ai`: passed against the installed local model. Returned a directly observed GCash reference with an exact evidence excerpt and source/record/timestamp references. This verifies transport and a narrow synthetic finding, not general model accuracy.
- `python -m pip check`: no broken requirements.
- Ruff unused-name checks and formatting; Python compilation; JavaScript `node --check`: passed in development.
- Real HTTP smoke on port 8001: login page 200; protected cases 401 without session; all seven local frontend assets 200.
- `START-CFAA.ps1 -Port 8001`: model check, migration and Uvicorn startup succeeded. Port 8000 was already occupied and was left alone. The launcher now reports Uvicorn exit failures correctly.
- Synthetic PDF rendered with PyMuPDF; every page visually inspected after layout iteration. DOCX opens and contains expected report sections, tables, chart and hash inventory in automated structural checks.

## Explicit limitations and remaining validation

- **No direct UFDR or HTML compatibility.** No vendor-certified Inseyets export fixture was provided. XML supports flat root-child records; nested exports retain original record XML but require validated mapping. Arbitrary fields/categories remain available rather than implying supported application-specific decoding.
- Multimedia support is exported metadata browsing, not binary decoding, EXIF acquisition, OCR, transcription or content analysis. No embeddings, advanced identity resolution, transaction verification, location map, or semantic financial/entity resolver is implemented. Crypto patterns identify candidates without checksum validation.
- **Browser interaction/visual testing was blocked:** the computer-use tool reported no available browsers or apps. API/HTML/static delivery and JavaScript syntax are verified; actual chart, graph, timeline, responsive/theme and browser download interaction still require manual QA.
- **DOCX visual QA is incomplete:** the packaged renderer failed because LibreOffice `soffice.exe` is unavailable. No privileged system installation was attempted. PDF visual QA is complete only for a synthetic Latin-script example. Standard PDF fonts may not cover non-Latin scripts.
- JSON and XML parsing are bounded in memory, not fully streaming. Upload limit 20 MiB, XLSX expanded-content limit 100 MiB, per-import record cap 50,000. Analysis views process the first 50,000 matching case artifacts and report when capped. Search/FTS index spans all committed artifacts. Timeline shows the current 200-row search page. Relationship drill-down loads at most 50 supporting artifacts per edge.
- AI retrieval considers at most 60 candidates and 12 ranked selections; final context is bounded to 3,500 UTF-8 bytes, individual excerpts 1,000 bytes, model query 800 bytes. Relevant later text may be omitted. Long input questions are preserved in history but shortened for inference. Model output can be wrong even with valid excerpts. The model has no tool interface; semantic prompt-injection immunity is not claimed.
- Endpoint clusters are connected recorded endpoints, not confirmed persons/organizations. Counter categories and directions depend on supplied labels. Unknown timezone timestamps are excluded from UTC date filters.
- Report drafts snapshot case details, source inventory and latest ten case AI analyses. Selected artifacts are immutable in the app, but OS/database administrators can tamper with storage. Exported DOCX edits are outside audit control. Approved report discovery/reopening is not yet provided in the browser; draft/export actions remain stored in database/audit.
- Single process, localhost deployment only. Login throttles/cancellation signals are process-local. No remote TLS deployment, user deactivation/reset UI, enterprise secret storage, tamper-evident audit chain, encryption-at-rest engine, automatic backups or independent security assessment. Use approved workstation ACLs, encryption and custody procedures. No ISO certification or legal-admissibility claim.
- ORM models use portable types, but MySQL migration/deployment has not been tested; FTS5 is SQLite-specific.
- Dependencies are recorded in requirements-lock.txt. Optional development render/lint utilities were installed locally but are not required by the application. No broad vulnerability audit or long-duration stress/soak test was performed.

## Start and evaluate

```powershell
Set-Location D:\GitHub-Projects\projectForensicAIAnalyzer
.\.venv\Scripts\python -m scripts.create_user admin --role admin
.\START-CFAA.ps1 -Port 8001
# Open http://127.0.0.1:8001; stop the server with Ctrl+C.
```

The account command prompts privately for a password of at least twelve characters. No default account/password was created. If a development server still owns port 8001, stop it in its terminal first, or choose another free loopback port. The default launcher port is 8000. Import tests/fixtures/demo.csv to evaluate with synthetic evidence. Review README.md and docs/SECURITY.md before considering real evidence.

## Login origin fix — 23 October 2026

Login forms now include a random, 15-minute nonce matched against an HttpOnly SameSite cookie. A valid form nonce permits login when an embedded browser sends an opaque or differing Origin; mismatched requests without the nonce remain rejected. Successful login clears the nonce cookie. Restart the server and reload the login page to obtain the updated form. Regression suite: 22 passed, one upstream test-client deprecation warning; includes opaque/webview origins, invalid/missing nonce cookies, and localhost/127.0.0.1 on ports 8000 and 8001.
