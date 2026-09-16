from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, SessionLocal, engine
from .models import *  # noqa: F401,F403 — Base.metadata에 테이블 등록
from .rag_chat_store import init_index
from .routers import attachments, auth, categories, cases, manual_chat, matches, sessions, solutions
from .routers.attachments import UPLOAD_DIR
from .seed import seed_categories

app = FastAPI(title="Carebridge API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_categories(db)
    init_index()  # 매뉴얼 인덱스를 미리 로딩해 첫 챗봇 요청 지연을 없앤다


@app.get("/health")
def health():
    return {"status": "ok"}
