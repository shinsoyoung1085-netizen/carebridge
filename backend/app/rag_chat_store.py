"""
매뉴얼 RAG 챗봇을 FastAPI 프로세스에 통합하기 위한 얇은 어댑터.

rag_engine.py(Streamlit 데모 app.py에서도 같은 모듈을 쓴다)를 그대로
재사용한다. 인덱스는 프로세스 시작 시 한 번만 로딩하고,
사용자별 대화 맥락(memory)은 user_id를 키로 하는 RAGEngine 인스턴스로 분리한다.
"""

from .rag_engine import RAGEngine, load_index

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
