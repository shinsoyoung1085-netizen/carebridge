import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .backup import start_backup_scheduler
from .database import Base, SessionLocal, engine
from .models import *  # noqa: F401,F403 — Base.metadata에 테이블 등록
from .rag_chat_store import init_index
from .routers import attachments, auth, categories, cases, manual_chat, matches, sessions, solutions
from .routers.attachments import UPLOAD_DIR
from .seed import seed_categories

logger = logging.getLogger("uvicorn.error")

app = FastAPI(title="Carebridge API", version="0.1.0")

# 쉼표로 구분한 프런트엔드 주소 목록. 예: "https://carebridge.vercel.app,http://localhost:5173"
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

app.include_router(auth.router)
app.include_router(categories.router)
app.include_router(cases.router)
app.include_router(matches.router)
app.include_router(sessions.router)
app.include_router(attachments.router)
app.include_router(solutions.router)
app.include_router(manual_chat.router)


@app.on_event("startup")
def on_startup():
    # 배포 환경에서 기동이 어느 단계에서 멈추는지 로그로 바로 알 수 있게 단계별로 남긴다.
    logger.info("DB 접속: %s", engine.url.render_as_string(hide_password=True))
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_categories(db)
    logger.info("DB 준비 완료, 매뉴얼 인덱스 로딩 시작")
    init_index()  # 매뉴얼 인덱스를 미리 로딩해 첫 챗봇 요청 지연을 없앤다
    logger.info("매뉴얼 인덱스 로딩 완료")
    # REQ-NFN-004. 관리형 DB 자체 백업을 쓰는 운영 환경에서는 BACKUP_ENABLED=false로 끈다.
    if os.getenv("BACKUP_ENABLED", "true").lower() != "false":
        app.state.backup_scheduler = start_backup_scheduler()


@app.on_event("shutdown")
def on_shutdown():
    scheduler = getattr(app.state, "backup_scheduler", None)
    if scheduler is not None:
        scheduler.shutdown(wait=False)


@app.get("/health")
def health():
    return {"status": "ok"}
