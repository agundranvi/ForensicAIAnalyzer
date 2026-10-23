# Security and evidence handling

Use only authorized evidence after validating this application with synthetic data. This development run does not authorize handling live sensitive case material. No evidence is uploaded to external AI services. Package and asset downloads during development contain no case content. Application frontend uses local assets and a self-only content security policy. All AI calls use the local loopback endpoint.

Sources are opened for writing only when a new random storage file is first created. Parsing and verification then use read-only file handles. Original external extraction files are never opened for writing. Uploaded copies have SHA-256 digests and provenance. Failed/cancelled sources are retained. The application does not enforce immutable storage against Windows users; use appropriate ACLs, approved write blockers and organizational chain-of-custody procedures. Hashes alone do not establish admissibility or chain of custody.

Authentication uses Argon2, random server-side sessions, eight-hour expiry, HttpOnly/SameSite cookies, CSRF checks and case authorization on evidence, AI, reports and audit routes. Administrators have all-case access by design. Sensitive values are not stored in frontend localStorage; only the theme preference is saved. Local HTTP is intended solely for the single-machine loopback deployment.

Controls include bounded requests, upload limits, random filenames, safe XML parsing, archive expansion/path checks, parameterized SQL, template autoescaping and textContent-based evidence rendering. Evidence never executes as HTML or spreadsheet formulas. Imported data cannot trigger model tools. Source records, derived indicators, AI history and investigator annotations remain separate.

Audit records cover login attempts, case changes, imports, search, hash verification, AI queries, report drafts/approvals/exports and financial export. Audit storage is local and mutable by administrators at the OS/database level. There is no tamper-evident audit chain, user deactivation UI, encrypted database, or enterprise key management. ISO/IEC 27037 alignment has not been independently assessed and no certification is claimed.

Git excludes .env, runtime data, databases, reports, logs, temporary files and Python caches. Review `git status --short` before any approved commit. Do not commit real evidence, personally identifiable information, passwords or operational secrets. No automatic commit, push or cloud synchronization is configured.
