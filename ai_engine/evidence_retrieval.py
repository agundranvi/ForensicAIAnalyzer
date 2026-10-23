import re
from sqlalchemy import select, text, or_
from app.database import Artifact


def retrieve(db, case_id, question):
    terms = list(dict.fromkeys(re.findall(r"\w{3,}", question.lower())))[:20]
    if not terms:
        return []
    if db.bind.dialect.name == "sqlite":
        expression = " OR ".join('"' + term.replace('"', '""') + '"' for term in terms)
        ids = list(
            db.execute(
                text(
                    "SELECT a.id FROM artifact_search s JOIN artifacts a ON a.id=s.rowid WHERE artifact_search MATCH :query AND a.case_id=:case_id ORDER BY rank LIMIT 60"
                ),
                {"query": expression, "case_id": case_id},
            ).scalars()
        )
        rows = list(
            db.scalars(
                select(Artifact).where(
                    Artifact.case_id == case_id, Artifact.id.in_(ids)
                )
            )
        )
    else:
        rows = list(
            db.scalars(
                select(Artifact)
                .where(
                    Artifact.case_id == case_id,
                    or_(*[Artifact.text.contains(t, autoescape=True) for t in terms]),
                )
                .limit(60)
            )
        )
    if not rows:
        rows = list(
            db.scalars(
                select(Artifact)
                .where(
                    Artifact.case_id == case_id,
                    or_(
                        *[
                            or_(
                                Artifact.text.contains(t, autoescape=True),
                                Artifact.sender.contains(t, autoescape=True),
                                Artifact.recipient.contains(t, autoescape=True),
                            )
                            for t in terms
                        ]
                    ),
                )
                .limit(60)
            )
        )
    return rows
