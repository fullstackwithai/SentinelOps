from pathlib import Path
from contextlib import asynccontextmanager
import csv
from datetime import datetime
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import get_settings
from app.core.database import Base, SessionLocal, engine, get_db
from app.core.models import InvestigationMessage, PlaybookDocument, SecurityEvent
from app.core.schemas import AlertFeatures, ChatRequest, ChatResponse, DashboardStats, PredictionResponse, ToolTrace
from app.services.agent import run_agent
from app.services.ml_service import MODEL_PATH, predict, train_model
from app.services.security_analytics import build_timeline

settings = get_settings()

@asynccontextmanager
async def lifespan(_: FastAPI):
    seed()
    yield

app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=settings.origin_list, allow_methods=["*"], allow_headers=["*"])
app.mount("/static", StaticFiles(directory="app/static"), name="static")


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(SecurityEvent).count() == 0:
            with open("data/sample_events.csv", newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    db.add(SecurityEvent(
                        timestamp=datetime.fromisoformat(row["timestamp"]), user=row["user"], source_ip=row["source_ip"],
                        event_type=row["event_type"], outcome=row["outcome"], country=row["country"],
                        privileged=int(row["privileged"]), device_new=int(row["device_new"]), hour=int(row["hour"]), risk_label=int(row["risk_label"]),
                    ))
        if db.query(PlaybookDocument).count() == 0:
            db.add(PlaybookDocument(filename="credential-compromise-playbook.md", content=Path("data/credential-compromise-playbook.md").read_text(encoding="utf-8")))
        db.commit()
    finally:
        db.close()


@app.get("/")
def home() -> FileResponse:
    return FileResponse("app/static/index.html")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "service": settings.app_name, "mode": "llm" if settings.openai_api_key else "offline-demo"}


@app.get("/api/stats", response_model=DashboardStats)
def stats(db: Session = Depends(get_db)) -> DashboardStats:
    events = db.query(SecurityEvent).count()
    failed = db.query(SecurityEvent).filter(SecurityEvent.outcome == "failure").count()
    high = db.query(SecurityEvent).filter(SecurityEvent.risk_label == 1).count()
    return DashboardStats(events=events, failed_events=failed, high_risk_events=high, playbooks=db.query(PlaybookDocument).count(), model_ready=MODEL_PATH.exists())


@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    answer, traces = run_agent(db, payload.session_id, payload.message)
    return ChatResponse(session_id=payload.session_id, answer=answer, traces=[ToolTrace(**t) for t in traces])


@app.get("/api/sessions/{session_id}")
def session(session_id: str, db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(InvestigationMessage).filter(InvestigationMessage.session_id == session_id).order_by(InvestigationMessage.id).limit(100).all()
    return [{"role": row.role, "content": row.content, "created_at": row.created_at.isoformat()} for row in rows]


@app.post("/api/playbooks")
async def upload_playbook(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    content = await file.read()
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise HTTPException(413, "File is too large.")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in {".txt", ".md"}:
        raise HTTPException(415, "Supported formats: .txt and .md")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise HTTPException(400, "File must be UTF-8.") from exc
    if not text.strip():
        raise HTTPException(400, "File is empty.")
    db.add(PlaybookDocument(filename=file.filename or "playbook", content=text))
    db.commit()
    return {"status": "indexed", "filename": file.filename, "characters": len(text)}


@app.get("/api/playbooks")
def playbooks(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(PlaybookDocument).order_by(PlaybookDocument.id.desc()).all()
    return [{"id": row.id, "filename": row.filename, "created_at": row.created_at.isoformat()} for row in rows]


@app.post("/api/ml/train")
def train() -> dict:
    return train_model()


@app.post("/api/ml/predict", response_model=PredictionResponse)
def ml_predict(payload: AlertFeatures) -> PredictionResponse:
    return PredictionResponse(**predict(payload.model_dump()))


@app.get("/api/timeline")
def timeline(user: str | None = None, db: Session = Depends(get_db)) -> list[dict]:
    return build_timeline(db, user=user)
