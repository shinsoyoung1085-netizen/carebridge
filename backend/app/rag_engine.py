"""
장기요양기관 시설급여 평가 매뉴얼 RAG 엔진.

data/manual.md 를 읽어 VectorStoreIndex를 구성하고, 질의에 대해
'답변 텍스트'와 '근거로 사용된 문서 청크(Source Node)'를 함께 반환한다.
"""

from __future__ import annotations

import logging
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
from llama_index.core.llms import MessageRole
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

# 검색된 발췌에 질문과 비슷한 단어만 있어도(예: 지표별 업무 주기, 직원 건강검진 주기)
# 그걸 질문의 답으로 옮겨 쓰는 오답이 있어, "질문의 대상과 발췌의 대상이 같은가"를
# 먼저 확인하도록 규칙을 명시한다.
SYSTEM_PROMPT = (
    "당신은 '2025년 장기요양기관 시설급여 평가 매뉴얼' 전문 안내 챗봇입니다.\n"
    "다음 규칙을 반드시 지키세요.\n"
    "1. 제공된 매뉴얼 발췌 내용만 근거로 답합니다. 일반 상식이나 추측으로 보충하지 않습니다.\n"
    "2. 답하기 전에 질문이 묻는 대상(무엇의 주기·횟수·기준·절차인지)과 발췌 내용이 다루는 대상이 "
    "같은지 확인합니다. 비슷한 단어가 있어도 대상이 다르면 근거로 쓰지 않습니다. "
    "예를 들어 특정 평가지표의 업무 주기나 직원 건강검진 주기를 기관 평가 자체의 주기로 답하면 안 됩니다.\n"
    "3. 질문이 일상 용어를 써도 매뉴얼 용어로 바꿔 이해합니다"
    "(예: 어르신·입소자 = 수급자, 재다 = 측정하다). 표현이 달라도 발췌에 답의 근거가 있으면 답합니다.\n"
    "4. 발췌 중 일부만 질문에 답하면 근거가 있는 부분만 답하고, 근거가 없는 부분은 매뉴얼에 없다고 밝힙니다.\n"
    "5. 발췌에 질문과 관련된 근거가 전혀 없을 때만 '매뉴얼에 나와있지 않은 내용입니다.'라고 답합니다.\n"
    "6. 답할 때는 근거가 된 평가지표나 기준을 함께 밝힙니다."
)


NOT_IN_MANUAL = "매뉴얼에 나와있지 않은 내용입니다."

# 매뉴얼은 '수급자'로 쓰는데 사용자는 '어르신'으로 묻는 경우가 많아 임베딩 검색에서
# 정답 조항이 밀려난다. 검색 전에 매뉴얼 용어를 덧붙여 재현율을 높인다.
MANUAL_TERMS = {
    "어르신": "수급자",
    "입소자": "수급자",
    "노인": "수급자",
}

# 답변 생성 후 한 번 더 확인하는 검증 프롬프트. 프롬프트 규칙만으로는 gpt-4o-mini가
# "평가 방법"을 "평가 주기"로 답하는 식의 대상 혼동을 완전히 막지 못해 별도 판정 단계를 둔다.
# 단, 조건을 엄격히 두면 맞는 답(표현만 다르거나 요약한 답)까지 NO가 나와 답변 전체가
# 거절 문구로 바뀌므로, 명백한 대상 혼동·근거 없는 내용만 걸러내도록 한다.
GROUNDING_CHECK_PROMPT = (
    "다음은 사용자 질문, 챗봇 답변, 답변의 근거로 검색된 매뉴얼 발췌입니다.\n"
    "아래 중 하나에 해당할 때만 NO, 그 외에는 YES로 판정하세요.\n"
    "(1) 답변이 질문과 다른 대상을 답한다"
    "(예: 평가 '주기'를 물었는데 평가 '방법'을 답함, 직원 건강검진 주기를 기관 평가 주기로 답함).\n"
    "(2) 답변의 핵심 내용(숫자·주기·기준)이 발췌 어디에도 없거나 발췌와 모순된다.\n"
    "표현이 다르거나(예: 어르신=수급자, 재다=측정), 발췌를 요약·재구성한 것은 NO 사유가 아닙니다.\n"
    "YES 또는 NO 한 단어로만 답하세요.\n\n"
    "[이전 질문]\n{history}\n\n[질문]\n{query}\n\n[답변]\n{answer}\n\n[발췌]\n{context}"
)


logger = logging.getLogger("carebridge.rag")
if not logger.handlers:
    logger.setLevel(logging.INFO)
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(_handler)


def _with_manual_terms(query: str) -> str:
    """질문에 쓰인 일상 용어에 대응하는 매뉴얼 용어를 괄호로 덧붙인다."""
    terms = sorted({term for word, term in MANUAL_TERMS.items() if word in query and term not in query})
    return f"{query} ({', '.join(terms)})" if terms else query


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
            # 매뉴얼에 같은 절이 중복 수록돼 상위 3개 중 2개가 같은 내용인 경우가 많아
            # 정답 조항이 검색에서 빠졌다. 후보를 넓혀 재현율을 높인다.
            similarity_top_k=6,
        )

    def chat(self, query: str) -> ChatResult:
        """질의에 대한 답변과, 답변 근거로 참조된 문서 청크 원문을 반환한다."""
        # "그럼 주기는요?" 같은 후속 질문을 검증 단계가 해석할 수 있도록 직전 질문들을 함께 넘긴다
        history = [m.content for m in self.memory.get() if m.role == MessageRole.USER][-2:]
        response = self.chat_engine.chat(_with_manual_terms(query))
        # 중복 수록된 절이 근거 목록에 반복 노출되지 않도록 순서를 유지한 채 중복 제거
        sources = list(dict.fromkeys(node.get_content().strip() for node in response.source_nodes))
        answer = str(response).strip()
        if answer.startswith(NOT_IN_MANUAL.rstrip(".")):
            logger.info("1차 답변에서 거절: %s", query)
        elif sources and not self._is_grounded(query, answer, sources, history):
            logger.info("검증 단계에서 거절: %s | 1차 답변: %s", query, answer)
            answer = NOT_IN_MANUAL
        return {"answer": answer, "sources": sources}

    @staticmethod
    def _is_grounded(query: str, answer: str, sources: list[str], history: list[str]) -> bool:
        """답변이 질문과 다른 대상을 답하거나 발췌에 없는 내용인지 LLM으로 한 번 더 판정한다."""
        verdict = Settings.llm.complete(
            GROUNDING_CHECK_PROMPT.format(
                history="\n".join(history) or "(없음)",
                query=query,
                answer=answer,
                # 자르면 뒤쪽 청크에 있는 정답 근거가 빠져 NO가 나오므로 전부 넘긴다 (6청크 ≈ 6천 자)
                context="\n---\n".join(sources),
            )
        )
        return not str(verdict).strip().upper().startswith("NO")

    def reset(self) -> None:
        """대화 기록(메모리)을 초기화한다."""
        self.chat_engine.reset()
