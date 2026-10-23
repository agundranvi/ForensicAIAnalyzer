import hashlib, json, secrets, time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException, UploadFile, File, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from argon2 import PasswordHasher
from sqlalchemy import select, func
from alembic.config import Config
from alembic import command
from app.config import ROOT, DATA, MAX_UPLOAD, CATEGORIES
from app.database import (
    DB,
    User,
    Session,
    Case,
    Evidence,
    Artifact,
    Audit,
    Analysis,
    Report,
)
from app.analytics import statistics, financial, clusters
from app.schemas import CaseCreate, CaseUpdate, Query, ReportDraft
from ai_engine.forensic_assistant import analyze
from ai_engine.evidence_retrieval import retrieve
from starlette.concurrency import run_in_threadpool


@asynccontextmanager
async def lifespan(app):
    cfg = Config(str(ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(ROOT / "migrations"))
    command.upgrade(cfg, "head")
    with DB() as db:
        for item in db.scalars(select(Evidence).where(Evidence.status == "processing")):
            item.status = "interrupted"
            item.summary = {"error": "Interrupted import; cancel then retry"}
        db.commit()
    yield


app = FastAPI(
    title="CICC Forensic AI Analyzer", lifespan=lifespan, docs_url=None, redoc_url=None
)
from app.security import BodyLimit

app.add_middleware(BodyLimit, limit=MAX_UPLOAD + 1024 * 1024)
app.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")
views = Jinja2Templates(directory=ROOT / "templates")
hasher = PasswordHasher()
failures = {}


def audit(db, user, action, case_id=None, detail=""):
    db.add(
        Audit(
            user_id=user.id if user else None,
            case_id=case_id,
            action=action,
            detail=detail,
        )
    )
    db.commit()


def database():
    with DB() as db:
        yield db


def auth(request: Request, db=Depends(database)):
    token = request.cookies.get("cfaa_session", "")
    s = db.get(Session, hashlib.sha256(token.encode()).hexdigest())
    if not s or s.expires < datetime.now(timezone.utc).replace(tzinfo=None):
        raise HTTPException(401, "Login required")
    if request.method not in ("GET", "HEAD", "OPTIONS") and not secrets.compare_digest(
        request.headers.get("x-csrf-token", ""), s.csrf
    ):
        raise HTTPException(403, "CSRF token required")
    request.state.csrf = s.csrf
    return db.get(User, s.user_id)


def case_access(db, user, case_id):
    c = db.get(Case, case_id)
    if not c or (user.role != "admin" and c.owner_id != user.id):
        raise HTTPException(404, "Case not found")
    return c


@app.middleware("http")
async def headers(request, call_next):
    if request.headers.get("host", "").split(":")[0] not in (
        "127.0.0.1",
        "localhost",
        "testserver",
    ):
        return Response(status_code=400)
    try:
        response = await call_next(request)
    except Exception:
        import logging

        logging.getLogger("cfaa").exception("Request failed")
        return Response("Internal error; consult administrator.", status_code=500)
    response.headers.update(
        {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "Cache-Control": "no-store",
            "Referrer-Policy": "no-referrer",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'",
        }
    )
    return response


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db=Depends(database)):
    try:
        user = auth(request, db)
    except HTTPException:
        login_csrf = secrets.token_hex(32)
        response = views.TemplateResponse(
            request,
            "login.html",
            {
                "setup": db.scalar(select(func.count(User.id))) == 0,
                "login_csrf": login_csrf,
            },
        )
        response.set_cookie(
            "cfaa_login_csrf", login_csrf, httponly=True, samesite="strict", max_age=900
        )
        return response
    return views.TemplateResponse(
        request,
        "index.html",
        {"user": user, "csrf": request.state.csrf, "categories": CATEGORIES},
    )


@app.post("/login")
def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    login_csrf: str = Form(default=""),
    db=Depends(database),
):
    origin = request.headers.get("origin")
    # Embedded browser views can send an opaque Origin ("null"). A fresh
    # form nonce, also present in an HttpOnly cookie, proves the form came
    # from this application without trusting an arbitrary Origin header.
    cookie_nonce = request.cookies.get("cfaa_login_csrf", "")
    valid_nonce = len(cookie_nonce) == 64 and secrets.compare_digest(
        cookie_nonce, login_csrf
    )
    if origin and origin != str(request.base_url).rstrip("/") and not valid_nonce:
        raise HTTPException(
            403,
            "Invalid origin. Reload the login page and submit its form, or open CFAA in your browser using the exact local URL.",
        )
    key = request.client.host
    history = [t for t in failures.get(key, []) if time.monotonic() - t < 300]
    if len(history) >= 10:
        raise HTTPException(429, "Too many attempts; wait five minutes")
    user = db.scalar(select(User).where(User.username == username))
    try:
        if not user:
            raise ValueError()
        hasher.verify(user.password, password)
    except Exception:
        failures[key] = history + [time.monotonic()]
        audit(db, None, "login_failed")
        raise HTTPException(401, "Invalid credentials")
    token = secrets.token_hex(32)
    db.add(
        Session(
            token=hashlib.sha256(token.encode()).hexdigest(),
            user_id=user.id,
            csrf=secrets.token_hex(32),
            expires=datetime.now(timezone.utc) + timedelta(hours=8),
        )
    )
    audit(db, user, "login")
    response = RedirectResponse("/", status_code=303)
    response.delete_cookie("cfaa_login_csrf")
    response.set_cookie(
        "cfaa_session", token, httponly=True, samesite="strict", max_age=28800
    )
    return response


@app.post("/api/logout")
def logout(request: Request, user=Depends(auth), db=Depends(database)):
    db.delete(
        db.get(
            Session,
            hashlib.sha256(request.cookies["cfaa_session"].encode()).hexdigest(),
        )
    )
    audit(db, user, "logout")
    response = Response(status_code=204)
    response.delete_cookie("cfaa_session")
    return response


@app.get("/api/cases")
def cases(user=Depends(auth), db=Depends(database)):
    query = select(Case)
    if user.role != "admin":
        query = query.where(Case.owner_id == user.id)
    return list(db.scalars(query.order_by(Case.id.desc())))


@app.post("/api/cases")
def create_case(payload: CaseCreate, user=Depends(auth), db=Depends(database)):
    v = payload.model_dump()
    if (
        not v.get("reference")
        or not v.get("title")
        or len(v["reference"]) > 100
        or len(v["title"]) > 250
    ):
        raise HTTPException(
            422, "Reference and title required (100/250 character limits)"
        )
    if db.scalar(select(Case).where(Case.reference == v["reference"])):
        raise HTTPException(409, "Reference already exists")
    c = Case(
        reference=v["reference"],
        title=v["title"],
        description=str(v.get("description", ""))[:20000],
        category=str(v.get("category", "Other"))[:100],
        owner_id=user.id,
    )
    db.add(c)
    db.commit()
    audit(db, user, "case_created", c.id)
    return c


@app.put("/api/cases/{case_id}")
def update_case(
    case_id: int, payload: CaseUpdate, user=Depends(auth), db=Depends(database)
):
    c = case_access(db, user, case_id)
    v = payload.model_dump(exclude_none=True)
    for field in ("notes", "device", "description"):
        if field in v:
            setattr(c, field, str(v[field])[:50000])
    if v.get("status") in ("active", "closed"):
        c.status = v["status"]
        c.closed = (
            datetime.now(timezone.utc).isoformat() if c.status == "closed" else ""
        )
    audit(db, user, "case_updated", case_id)
    return c


@app.post("/api/cases/{case_id}/imports")
async def upload(
    case_id: int, file: UploadFile = File(...), user=Depends(auth), db=Depends(database)
):
    case_access(db, user, case_id)
    name = Path((file.filename or "").replace("\\", "/")).name[:255]
    ext = Path(name).suffix.lower()
    if ext not in (".csv", ".xlsx", ".json", ".xml"):
        raise HTTPException(415, "Supported: CSV, XLSX, JSON, XML")
    path = DATA / (secrets.token_hex(20) + ".source")
    digest = hashlib.sha256()
    size = 0
    try:
        with path.open("xb") as out:
            while chunk := await file.read(65536):
                size += len(chunk)
                if size > MAX_UPLOAD:
                    raise HTTPException(413, "20 MiB upload limit")
                digest.update(chunk)
                out.write(chunk)
    except Exception:
        path.unlink(missing_ok=True)
        raise
    duplicate = db.scalar(
        select(Evidence).where(
            Evidence.case_id == case_id,
            Evidence.digest == digest.hexdigest(),
            Evidence.status != "cancelled",
        )
    )
    if duplicate:
        path.unlink()
        raise HTTPException(409, f"Duplicate import {duplicate.id}")
    evidence = Evidence(
        case_id=case_id, filename=name, digest=digest.hexdigest(), path=str(path)
    )
    db.add(evidence)
    db.commit()
    from app.importing import process

    return await run_in_threadpool(process, evidence.id, ext, user.id)


@app.get("/api/cases/{case_id}/imports")
def imports(case_id: int, user=Depends(auth), db=Depends(database)):
    case_access(db, user, case_id)
    return [
        dict(
            id=e.id,
            filename=e.filename,
            digest=e.digest,
            status=e.status,
            summary=e.summary,
            created=e.created,
        )
        for e in db.scalars(select(Evidence).where(Evidence.case_id == case_id))
    ]


@app.post("/api/cases/{case_id}/imports/{import_id}/{action}")
def integrity(
    case_id: int, import_id: int, action: str, user=Depends(auth), db=Depends(database)
):
    case_access(db, user, case_id)
    e = db.get(Evidence, import_id)
    if not e or e.case_id != case_id:
        raise HTTPException(404)
    if action == "verify":
        digest = hashlib.sha256()
        try:
            with Path(e.path).open("rb") as f:
                while chunk := f.read(65536):
                    digest.update(chunk)
            valid = digest.hexdigest() == e.digest
        except OSError:
            valid = False
        audit(
            db,
            user,
            "integrity_verified",
            case_id,
            json.dumps({"import": e.id, "valid": valid}),
        )
        return {"valid": valid, "sha256": e.digest}
    if action == "cancel":
        from app.importing import request_cancel

        if e.status == "processing":
            if request_cancel(e.id):
                return {"status": "cancellation_requested"}
            db.refresh(e)
            if e.status == "processing":
                raise HTTPException(
                    409, "Import worker is starting or finishing; retry shortly"
                )
        if e.status == "complete":
            raise HTTPException(409, "Completed imports cannot be cancelled")
        e.status = "cancelled"
        audit(db, user, "import_cancelled", case_id, str(e.id))
        return {"status": e.status}
    raise HTTPException(404)


def artifacts_query(
    db,
    case_id,
    q="",
    category="",
    contact="",
    direction="",
    application="",
    start="",
    end="",
):
    query = select(Artifact).where(Artifact.case_id == case_id)
    if q:
        query = query.where(Artifact.text.contains(q, autoescape=True))
    if category:
        query = query.where(Artifact.category == category)
    if contact:
        query = query.where(
            (Artifact.sender.contains(contact, autoescape=True))
            | (Artifact.recipient.contains(contact, autoescape=True))
        )
    for column, value in (
        (Artifact.direction, direction),
        (Artifact.application, application),
    ):
        if value:
            query = query.where(column == value)
    if start:
        query = query.where(Artifact.timestamp_utc >= start)
    if end:
        query = query.where(Artifact.timestamp_utc <= end)
    return query


@app.get("/api/cases/{case_id}/artifacts")
def artifacts(
    case_id: int,
    q: str = "",
    category: str = "",
    contact: str = "",
    direction: str = "",
    application: str = "",
    start: str = "",
    end: str = "",
    offset: int = 0,
    user=Depends(auth),
    db=Depends(database),
):
    case_access(db, user, case_id)
    audit(db, user, "evidence_searched", case_id)
    return list(
        db.scalars(
            artifacts_query(
                db, case_id, q, category, contact, direction, application, start, end
            )
            .order_by(Artifact.timestamp_utc, Artifact.id)
            .offset(max(0, offset))
            .limit(200)
        )
    )


@app.get("/api/cases/{case_id}/analysis")
def dashboard(
    case_id: int,
    q: str = "",
    category: str = "",
    contact: str = "",
    direction: str = "",
    application: str = "",
    start: str = "",
    end: str = "",
    user=Depends(auth),
    db=Depends(database),
):
    case_access(db, user, case_id)
    query = artifacts_query(
        db, case_id, q, category, contact, direction, application, start, end
    )
    total = db.scalar(select(func.count()).select_from(query.subquery()))
    rows = list(db.scalars(query.order_by(Artifact.id).limit(50000)))
    edges = {}
    for a in rows:
        if a.sender and a.recipient:
            edges.setdefault((a.sender, a.recipient), []).append(a.id)
    return {
        "total": total,
        "processed": len(rows),
        "limited": len(rows) < total,
        "statistics": statistics(rows),
        "clusters": clusters(edges),
        "financial": financial(rows),
        "links": [
            {"source": k[0], "target": k[1], "artifact_ids": v}
            for k, v in edges.items()
        ],
        "ai_count": db.scalar(
            select(func.count(Analysis.id)).where(Analysis.case_id == case_id)
        ),
    }


@app.post("/api/cases/{case_id}/ask")
async def ask(case_id: int, payload: Query, user=Depends(auth), db=Depends(database)):
    case_access(db, user, case_id)
    question = payload.question
    if not question or len(question) > 2000:
        raise HTTPException(422, "Question required, maximum 2000 characters")
    rows = retrieve(db, case_id, question)
    try:
        result = await run_in_threadpool(analyze, question, rows)
    except Exception:
        db.add(
            Analysis(
                case_id=case_id,
                user_id=user.id,
                question=question,
                result={
                    "message": "Local model unavailable or returned invalid output",
                    "findings": [],
                    "status": "failed",
                },
            )
        )
        audit(db, user, "ai_query_failed", case_id)
        raise HTTPException(502, "Local model unavailable or returned invalid output")
    db.add(Analysis(case_id=case_id, user_id=user.id, question=question, result=result))
    audit(db, user, "ai_query", case_id)
    return result


@app.get("/api/cases/{case_id}/history")
def history(case_id: int, user=Depends(auth), db=Depends(database)):
    case_access(db, user, case_id)
    return list(
        db.scalars(
            select(Analysis)
            .where(Analysis.case_id == case_id)
            .order_by(Analysis.id.desc())
            .limit(100)
        )
    )


@app.get("/api/cases/{case_id}/audit")
def logs(case_id: int, user=Depends(auth), db=Depends(database)):
    case_access(db, user, case_id)
    return list(
        db.scalars(
            select(Audit)
            .where(Audit.case_id == case_id)
            .order_by(Audit.id.desc())
            .limit(200)
        )
    )


@app.post("/api/cases/{case_id}/reports")
def report_draft(
    case_id: int, payload: ReportDraft, user=Depends(auth), db=Depends(database)
):
    c = case_access(db, user, case_id)
    v = payload.model_dump(exclude_none=True)
    ids = v.get("artifact_ids", [])
    if not isinstance(ids, list) or len(ids) > 200:
        raise HTTPException(422, "Select at most 200 artifact IDs")
    selected = list(
        db.scalars(
            select(Artifact).where(Artifact.case_id == case_id, Artifact.id.in_(ids))
        )
    )
    if set(ids) != {a.id for a in selected}:
        raise HTTPException(422, "Invalid artifact selection")
    body = str(v.get("body", ""))[:100000]
    snapshot = {
        "sources": [
            {"id": e.id, "filename": e.filename, "digest": e.digest, "status": e.status}
            for e in db.scalars(select(Evidence).where(Evidence.case_id == case_id))
        ],
        "analyses": [
            {"id": a.id, "question": a.question, "result": a.result}
            for a in db.scalars(
                select(Analysis)
                .where(Analysis.case_id == case_id)
                .order_by(Analysis.id.desc())
                .limit(10)
            )
        ],
        "case": {
            "reference": c.reference,
            "title": c.title,
            "category": c.category,
            "opened": str(c.opened),
            "device": c.device,
            "description": c.description,
        },
    }
    r = Report(
        case_id=case_id, user_id=user.id, body=body, artifact_ids=ids, snapshot=snapshot
    )
    db.add(r)
    audit(db, user, "report_drafted", case_id)
    return r


@app.post("/api/cases/{case_id}/reports/{report_id}/approve")
def approve(case_id: int, report_id: int, user=Depends(auth), db=Depends(database)):
    case_access(db, user, case_id)
    r = db.get(Report, report_id)
    if not r or r.case_id != case_id:
        raise HTTPException(404)
    r.approved = 1
    audit(db, user, "report_approved", case_id, str(r.id))
    return {"approved": True}


@app.get("/api/cases/{case_id}/reports/{report_id}/{format}")
def export(
    case_id: int, report_id: int, format: str, user=Depends(auth), db=Depends(database)
):
    c = case_access(db, user, case_id)
    r = db.get(Report, report_id)
    if not r or r.case_id != case_id:
        raise HTTPException(404)
    if not r.approved:
        raise HTTPException(409, "Review and approve report before export")
    from app.reporting import generate

    rows = list(
        db.scalars(
            select(Artifact).where(
                Artifact.case_id == case_id, Artifact.id.in_(r.artifact_ids)
            )
        )
    )
    from types import SimpleNamespace

    sources = [SimpleNamespace(**e) for e in r.snapshot.get("sources", [])]
    c = SimpleNamespace(**r.snapshot["case"]) if r.snapshot.get("case") else c
    if format not in ("pdf", "docx"):
        raise HTTPException(404)
    content = generate(c, r, rows, sources, format)
    audit(db, user, "report_exported", case_id, f"{r.id}:{format}")
    return Response(
        content,
        media_type="application/pdf"
        if format == "pdf"
        else "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f'attachment; filename="case-{case_id}-report-{report_id}.{format}"'
        },
    )


@app.get("/api/overview")
def overview(user=Depends(auth), db=Depends(database)):
    allowed = select(Case.id)
    if user.role != "admin":
        allowed = allowed.where(Case.owner_id == user.id)
    ids = list(db.scalars(allowed))
    return {
        "total_cases": len(ids),
        "active_cases": db.scalar(
            select(func.count(Case.id)).where(Case.id.in_(ids), Case.status == "active")
        ),
        "evidence_sources": db.scalar(
            select(func.count(Evidence.id)).where(Evidence.case_id.in_(ids))
        ),
        "indexed_artifacts": db.scalar(
            select(func.count(Artifact.id)).where(Artifact.case_id.in_(ids))
        ),
        "ai_analyses": db.scalar(
            select(func.count(Analysis.id)).where(Analysis.case_id.in_(ids))
        ),
    }


@app.get("/api/users")
def users(user=Depends(auth), db=Depends(database)):
    if user.role != "admin":
        raise HTTPException(403, "Administrator required")
    return [
        dict(id=u.id, username=u.username, role=u.role)
        for u in db.scalars(select(User))
    ]


@app.post("/api/cases/{case_id}/assign/{owner_id}")
def assign(case_id: int, owner_id: int, user=Depends(auth), db=Depends(database)):
    if user.role != "admin":
        raise HTTPException(403, "Administrator required")
    c = case_access(db, user, case_id)
    if not db.get(User, owner_id):
        raise HTTPException(404, "User not found")
    c.owner_id = owner_id
    audit(db, user, "case_assigned", case_id, str(owner_id))
    return c


@app.get("/api/cases/{case_id}/financial-export")
def financial_export(case_id: int, user=Depends(auth), db=Depends(database)):
    case_access(db, user, case_id)
    rows = list(
        db.scalars(select(Artifact).where(Artifact.case_id == case_id).limit(50000))
    )
    audit(db, user, "financial_exported", case_id)
    return Response(
        json.dumps(financial(rows)),
        media_type="application/json",
        headers={
            "Content-Disposition": f'attachment; filename="case-{case_id}-indicators.json"'
        },
    )


@app.get("/api/cases/{case_id}/artifacts/{artifact_id}")
def artifact_detail(
    case_id: int, artifact_id: int, user=Depends(auth), db=Depends(database)
):
    case_access(db, user, case_id)
    artifact = db.get(Artifact, artifact_id)
    if not artifact or artifact.case_id != case_id:
        raise HTTPException(404, "Artifact not found")
    audit(db, user, "artifact_viewed", case_id, str(artifact_id))
    return artifact
