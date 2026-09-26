"""
장기요양기관 시설급여 평가 매뉴얼 챗봇 — Streamlit 웹 UI.
"""

import streamlit as st

from backend.app.rag_engine import RAGEngine, load_index

st.set_page_config(
    page_title="장기요양기관 평가 매뉴얼 챗봇",
    page_icon="🏥",
    layout="centered",
)

SAMPLE_QUESTIONS = [
    "시설급여 평가는 몇 년 주기로 실시되나요?",
    "평가 등급은 어떻게 구분되나요?",
    "평가 결과에 이의가 있으면 어떻게 해야 하나요?",
]

USER_AVATAR = "🧑"
ASSISTANT_AVATAR = "🏥"


@st.cache_resource(show_spinner="매뉴얼을 읽어오는 중입니다...")
def get_index():
    """인덱스는 모든 세션이 공유해도 되는 읽기 전용 데이터이므로 캐시한다."""
    return load_index()


def init_session_state() -> None:
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None
    if "engine" not in st.session_state:
        st.session_state.engine = RAGEngine(get_index())


def render_sources(sources: list[str]) -> None:
    if not sources:
        return
    with st.expander("📚 참고한 매뉴얼 내용 보기"):
        for i, src in enumerate(sources, start=1):
            st.markdown(f"**출처 {i}**")
            st.markdown(src)
            if i < len(sources):
                st.divider()


def render_sidebar() -> None:
    with st.sidebar:
        st.header("🏥 매뉴얼 안내 챗봇")
        st.write(
            "**2025년 장기요양기관 시설급여 평가 매뉴얼** 내용을 바탕으로 "
            "질문에 답변하는 챗봇입니다.\n\n"
            "매뉴얼에 근거가 없는 내용은 추측 없이 "
            "'매뉴얼에 나와있지 않은 내용입니다'라고 답변합니다."
        )

        st.divider()
        st.subheader("💡 추천 질문")
        for question in SAMPLE_QUESTIONS:
            if st.button(question, use_container_width=True, key=f"sample_{question}"):
                st.session_state.pending_question = question

        st.divider()
        if st.button("🗑️ 대화 초기화", use_container_width=True):
            st.session_state.messages = []
            st.session_state.engine.reset()
            st.rerun()


def render_history() -> None:
    for message in st.session_state.messages:
        avatar = USER_AVATAR if message["role"] == "user" else ASSISTANT_AVATAR
        with st.chat_message(message["role"], avatar=avatar):
            st.markdown(message["content"])
            if message["role"] == "assistant":
                render_sources(message.get("sources", []))


def handle_question(question: str) -> None:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(question)

    with st.chat_message("assistant", avatar=ASSISTANT_AVATAR):
        with st.spinner("매뉴얼을 검토하는 중입니다..."):
            result = st.session_state.engine.chat(question)
        st.markdown(result["answer"])
        render_sources(result["sources"])

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["answer"],
            "sources": result["sources"],
        }
    )


def main() -> None:
    st.title("🏥 장기요양기관 평가 매뉴얼 챗봇")
    st.caption("2025년 장기요양기관 시설급여 평가 매뉴얼 기반 Q&A")

    try:
        init_session_state()
    except (RuntimeError, FileNotFoundError) as error:
        st.error(str(error))
        st.stop()

    render_sidebar()
    render_history()

    question = st.chat_input("궁금한 내용을 입력하세요 (예: 평가 주기는 어떻게 되나요?)")

    if st.session_state.pending_question:
        question = st.session_state.pending_question
        st.session_state.pending_question = None

    if question:
        handle_question(question)


if __name__ == "__main__":
    main()
