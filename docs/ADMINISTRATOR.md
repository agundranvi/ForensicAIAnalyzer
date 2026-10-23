# Administrator guide

Provision accounts from the local console using `python -m scripts.create_user NAME --role investigator` or `--role admin`. Passwords are Argon2 hashed. Case assignment is available through administrator-only API `POST /api/cases/{case_id}/assign/{user_id}`; retrieve IDs from `GET /api/users`. All mutations require the current server-session CSRF token from the authenticated page. The Case notes panel includes an administrator assignment button. Browser account provisioning is not yet provided.

Configuration uses process environment variables, read before application import. `.env.example` is documentation; `.env` is not automatically loaded. `CFAA_DATA_DIR` selects source storage. `CFAA_DATABASE_URL` selects SQLAlchemy database URL. Default SQLite file is data/cfaa.db. Keep the database and evidence directory together in backups. Environment settings containing credentials must never be committed.

Stop the app before copying the data directory to an authorized encrypted backup location. Back up before migration. Run `python -m alembic upgrade head` to migrate. Destructive downgrades are disabled. Restore into a separate location, configure it, and verify inventory hashes before switching. Test restore procedures on synthetic data. Audit records share the database; they are not tamper-proof against an operating-system administrator.

Use one Uvicorn worker. Cancellation state and login attempt rate limits are process-local. No distributed deployment is supported. MySQL-oriented ORM types are used, but MySQL deployment and migrations have not been validated. SQLite FTS5 indexing is platform-specific; other databases use bounded LIKE retrieval.

The HTTP session cookie is HttpOnly and SameSite=Strict. Secure-cookie mode/TLS and remote deployment are not implemented; keep localhost binding. Restrict Windows filesystem access to authorized operators and use approved full-disk encryption. No default password exists.

Set CFAA_CATEGORIES to a JSON list of category names before startup to customize the case creation menu. Invalid lists stop startup with a clear error.
