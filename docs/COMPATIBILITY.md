# Cellebrite export compatibility

Verified fixtures are synthetic, not vendor-certified exports. The generic adapters accept common tabular export fields; compatibility with an actual Cellebrite Inseyets version has not been verified. No direct UFDR, proprietary database, encrypted extraction or HTML parser is provided. Do not rename UFDR files to accepted extensions.

CSV: UTF-8 with header row; duplicate headers and overflow fields fail visibly. XLSX: each worksheet has a header row; source references include worksheet and row. Formulas are preserved as text, never evaluated. ZIP entries are never extracted; expansion and entry-count limits are checked. JSON: list of objects, or object containing `artifacts` or `records`; a single object is preserved as one artifact. XML: direct children of the root are records; immediate fields are normalized and complete record XML is preserved under `_xml`. XML entities/external references are rejected. Deep proprietary XML structures require a validated adapter; they are not silently interpreted as supported messages.

Recognized fields (case insensitive, spaces mapped to underscores):

| Normalized field | Export aliases |
| --- | --- |
| Category | category, type, artifact_type, XML record tag |
| Sender | sender, from, source, phone, name |
| Recipient | recipient, to, destination |
| Body | text, body, message, content, url, description |
| Timestamp | timestamp, date, time, datetime, date/time |
| Application | application, app |
| Direction | direction |

All original fields and values are retained. Categories such as SMS, MMS, calls, contacts, emails, browser, downloads, multimedia/file metadata, locations, app usage, device and social/chat artifacts can be represented when exported. Labels are retained, not inferred from an app installation. Missing categories are labeled unsupported. Multimedia analysis currently covers exported metadata fields, not binary media decoding, OCR, audio transcription or EXIF acquisition. Category-specific nested data adapters require validated source fixtures.

ISO-8601 timestamps with explicit offsets normalize to UTC. Ambiguous or unknown timezones are never assumed. Original timestamp representations remain available. No source files are rewritten. Each import is atomic and has a visible completed/failed/cancelled/interrupted status. Uploads are bounded; CSV/XLSX iterate records and flush batches. JSON/XML are bounded in-memory parsing, not unbounded streaming.
