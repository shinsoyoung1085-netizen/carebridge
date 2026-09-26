"""
장기요양기관 시설급여 평가 매뉴얼 RAG 엔진.

data/manual.md 를 읽어 VectorStoreIndex를 구성하고, 질의에 대해
'답변 텍스트'와 '근거로 사용된 문서 청크(Source Node)'를 함께 반환한다.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TypedDict

from dotenv import load_dotenv
from llama_index.core import (
    Settings,
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
    load_index_from_storage,
)
from llama_index.core.memory import ChatMemoryBuffer
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

load_dotenv(override=True)  # 셸에 이미 설정된 OPENAI_API_KEY보다 .env 값을 우선한다

# backend/app/rag_engine.py -> parents[1] == backend/
BACKEND_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BACKEND_DIR / "data"
STORAGE_DIR = BACKEND_DIR / "storage"

LLM_MODEL = "gpt-4o-mini"
EMBED_MODEL = "text-embedding-3-small"

SYSTEM_PROMPT = (
    "당신은 '2025년 장기요양기관 시설급여 평가 매뉴얼' 전문 안내 챗봇입니다. "
    "제공된 문서 내용에 기반해서만 사실에 입각하여 답변하세요. "
    "매뉴얼에 없는 내용은 추측하지 말고 "
    "'매뉴얼에 나와있지 않은 내용입니다'라고 명확히 밝히세요."
)


class ChatResult(TypedDict):
    answer: str
    sources: list[str]


def _configure_settings() -> None:
    """OpenAI LLM·임베딩 모델을 llama-index 전역 Settings에 등록한다."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "OPENAI_API_KEY가 설정되어 있지 않습니다. .env 파일을 확인해주세요."
        )
    Settings.llm = OpenAI(model=LLM_MODEL, temperature=0, api_key=api_key)
    Settings.embed_model = OpenAIEmbedding(
        model=EMBED_MODEL,
        api_key=api_key,
        embed_batch_size=20,  # 계정의 분당 토큰 한도(TPM)를 넘지 않도록 배치를 작게 유지
    )


def load_index() -> VectorStoreIndex:
    """data/manual.md로부터 인덱스를 생성하거나, 저장된 인덱스를 불러온다.

    한 번 생성된 인덱스는 storage/ 에 저장해 재실행 시 임베딩 비용을 아낀다.
    """
    _configure_settings()

    if STORAGE_DIR.exists():
        storage_context = StorageContext.from_defaults(persist_dir=str(STORAGE_DIR))
        return load_index_from_storage(storage_context)

    if not DATA_DIR.exists() or not any(DATA_DIR.iterdir()):
        raise FileNotFoundError(
            f"'{DATA_DIR}/' 폴더에서 매뉴얼 파일을 찾을 수 없습니다. "
            f"'{DATA_DIR}/manual.md' 파일을 준비해주세요."
        )

    documents = SimpleDirectoryReader(str(DATA_DIR)).load_data()
    index = VectorStoreIndex.from_documents(documents)
    index.storage_context.persist(persist_dir=str(STORAGE_DIR))
    return index


class RAGEngine:
    """세션(대화) 단위로 사용하는 RAG 챗 엔진.

    동일 인스턴스에 연속으로 chat()을 호출하면 대화 맥락(Context)이 유지된다.
    """

    def __init__(self, index: VectorStoreIndex):
        self.memory = ChatMemoryBuffer.from_defaults(token_limit=3900)
        self.chat_engine = index.as_chat_engine(
            chat_mode="context",
            memory=self.memory,
            system_prompt=SYSTEM_PROMPT,
            similarity_top_k=3,
        )

    def chat(self, query: str) -> ChatResult:
        """질의에 대한 답변과, 답변 근거로 참조된 문서 청크 원문을 반환한다."""
        response = self.chat_engine.chat(query)
        sources = [node.get_content().strip() for node in response.source_nodes]
        return {"answer": str(response).strip(), "sources": sources}

    def reset(self) -> None:
        """대화 기록(메모리)을 초기화한다."""
        self.chat_engine.reset()
