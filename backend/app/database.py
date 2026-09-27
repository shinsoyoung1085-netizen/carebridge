import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv(override=True)

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://localhost/carebridge",
)
# 대시보드에 붙여넣을 때 섞여 들어오기 쉬운 공백·줄바꿈·따옴표·백틱을 제거한다.
DATABASE_URL = DATABASE_URL.strip().strip("`'\"").strip()
# Render·Heroku는 "postgres://", Supabase는 드라이버 없는 "postgresql://" 형식으로 준다.
# SQLAlchemy 2.1부터 드라이버 미지정 시 psycopg(v3)를 기본으로 쓰는데, 설치된 건 psycopg2라
# 드라이버를 명시해 둔다.
for prefix in ("postgres://", "postgresql://"):
    if DATABASE_URL.startswith(prefix):
        DATABASE_URL = "postgresql+psycopg2://" + DATABASE_URL[len(prefix):]
        break

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
