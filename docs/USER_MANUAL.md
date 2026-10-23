# User manual

Sign in with a locally provisioned account. Administrators can view all cases; investigators can view only their assigned cases. Case creation assigns the current user. Use unique case references and synthetic exports for familiarization.

Try `tests/fixtures/demo.csv` for a synthetic example.

Evidence import accepts UTF-8 CSV, XLSX, flat JSON or flat XML. Upload at most 20 MiB and 50,000 records. Originals are stored under random filenames with a SHA-256 digest; the original filename remains in the inventory. Unsupported category records are retained. A failed import publishes no artifacts and retains its original with a visible error. Duplicate hashes are rejected within the same case. Failed/interrupted imports can be cancelled and retried. Active import cancellation takes effect at the next record boundary; it is not a process termination.

Search supports text, exact category/application/direction, contact substring and UTC date bounds. Results page in batches of 200. Use ISO timestamp bounds including timezone. Date filters omit records without a normalized UTC timestamp; inspect these separately. Select an artifact ID to view original fields and source record. Checkboxes persist across pages within a selected case, up to 200 report references.

Analysis shows all indexed case artifacts up to the documented 50,000 artifact analysis cap. Endpoint counts count recorded sender and recipient appearances, not unique people. Graph edges have supporting artifact IDs. Timeline uses the currently loaded search page, with uncertain timestamps listed separately. It supports zoom and selection. Financial matches are unverified text indicators; crypto candidates are not checksum validated.

AI retrieval uses the case-scoped SQLite full-text index with a substring fallback, then a small deterministic evidence selection. Evidence excerpts have a conservative input byte budget and can omit relevant later text. Ask narrow questions and manually search if an answer is insufficient. Every accepted finding includes source and record references plus an exact excerpt. An excerpt match does not validate the model interpretation. AI responses and questions remain in local case history.

Write report findings in the editor, save a draft, review it and approve. Changing the editor invalidates its approval controls until a new draft is saved. Exports include the saved snapshot, selected artifacts and source hashes. DOCX remains editable after export; externally edited versions are outside application audit control. AI observations included in your narrative must be explicitly labeled. Never infer guilt or identity from automated summaries.

Use Case notes for investigator notes, device information and closure status. Sign out to invalidate the session; sessions expire after eight hours.
