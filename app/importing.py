"""Bounded transactional import worker; originals are never rewritten."""

import threading
from collections import Counter
from app.database import DB, Evidence, Artifact, Audit
from parsers.cellebrite_adapter import records, normalize, LIMIT

cancel_events = {}
lock = threading.Lock()


class Cancelled(Exception):
    pass


def process(import_id, extension, user_id):
    event = threading.Event()
    with lock:
        cancel_events[import_id] = event
    with DB() as db:
        source = db.get(Evidence, import_id)
        count = 0
        warnings = []
        categories = Counter()
        try:
            from pathlib import Path

            for ref, row in records(Path(source.path), extension):
                if event.is_set():
                    raise Cancelled("Import cancelled by investigator")
                count += 1
                if count > LIMIT:
                    raise ValueError("50,000 record limit exceeded; split the export")
                value = normalize(row)
                categories[value["category"]] += 1
                if value["category"] == "unsupported" and len(warnings) < 100:
                    warnings.append(
                        f"Record {ref}: category unavailable; all values preserved"
                    )
                db.add(
                    Artifact(
                        case_id=source.case_id,
                        evidence_id=source.id,
                        source_ref=ref,
                        **value,
                    )
                )
                if count % 500 == 0:
                    db.flush()
            if event.is_set():
                raise Cancelled("Import cancelled by investigator")
            if not count:
                raise ValueError("No records found")
            source.status = "complete"
            source.summary = {
                "records": count,
                "categories": dict(categories),
                "warnings": warnings,
            }
            db.add(
                Audit(
                    user_id=user_id,
                    case_id=source.case_id,
                    action="import_complete",
                    detail=str(source.id),
                )
            )
            db.commit()
        except Exception as exc:
            db.rollback()
            source = db.get(Evidence, import_id)
            source.status = "cancelled" if isinstance(exc, Cancelled) else "failed"
            source.summary = {"error": str(exc)[:500], "records": 0}
            db.add(
                Audit(
                    user_id=user_id,
                    case_id=source.case_id,
                    action="import_" + source.status,
                    detail=str(source.id),
                )
            )
            db.commit()
        finally:
            with lock:
                cancel_events.pop(import_id, None)
        return dict(
            id=source.id,
            case_id=source.case_id,
            filename=source.filename,
            digest=source.digest,
            status=source.status,
            summary=source.summary,
            created=source.created,
        )


def request_cancel(import_id):
    with lock:
        event = cancel_events.get(import_id)
        if event:
            event.set()
            return True
    return False
