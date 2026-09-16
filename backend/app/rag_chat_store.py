"""
매뉴얼 RAG 챗봇을 FastAPI 프로세스에 통합하기 위한 얇은 어댑터.

rag_engine.py(프로젝트 루트, Streamlit 데모에서 쓰던 것과 동일 모듈)를
그대로 재사용한다. 인덱스는 프로세스 시작 시 한 번만 로딩하고,
사용자별 대화 맥락(memory)은 user_id를 키로 하는 RAGEngine 인스턴스로 분리한다.
"""

import sys
from pathlib import Path

# rag_engine.py는 backend/ 상위(프로젝트 루트)에 있다.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rag_engine import RAGEngine, load_index  # noqa: E402

_index = None
_engines: dict[int, RAGEngine] = {}


def init_index():
    """앱 시작 시 인덱스를 미리 로딩해 첫 요청 지연을 없앤다."""
    global _index
    if _index is None:
        _index = load_index()
    return _index


def get_engine(user_id: int) -> RAGEngine:
    if user_id not in _engines:
        _engines[user_id] = RAGEngine(init_index())
    return _engines[user_id]


def reset_engine(user_id: int) -> None:
    if user_id in _engines:
        _engines[user_id].reset()
