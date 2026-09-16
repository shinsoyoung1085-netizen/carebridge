import * as React from "react";
import { api, ApiError } from "../api/client";
import type { ChatResponse } from "../api/types";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: string[];
}

const SAMPLE_QUESTIONS = [
  "어르신 체중은 한달에 몇번재야하나요?",
  "이용자 평가는 어떤방식으로 이루어지나요?",
  "목욕은 한달에 몇번시켜야하나요?",
];

export function ManualChatPage() {
  const [messages, setMessages] = React.useState<ChatMessage[]>([]);
  const [input, setInput] = React.useState("");
  const [sending, setSending] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [openSources, setOpenSources] = React.useState<Set<number>>(new Set());
  const bottomRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send(text: string) {
    const question = text.trim();
    if (!question || sending) return;

    setError(null);
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setSending(true);
    try {
      const res = await api.post<ChatResponse>("/manual/chat", { message: question });
      setMessages((prev) => [...prev, { role: "assistant", content: res.answer, sources: res.sources }]);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "답변을 가져오지 못했습니다.";
      setError(message);
      setMessages((prev) => [...prev, { role: "assistant", content: `⚠️ ${message}` }]);
    } finally {
      setSending(false);
    }
  }

  function toggleSources(index: number) {
    setOpenSources((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  }

  return (
    <div className="page page-chat">
      <h1>🏥 편하게 물어보세요</h1>
      <p className="page-sub">2025년 장기요양기관 시설급여 평가 매뉴얼 기반 Q&amp;A</p>

      {messages.length === 0 && (
        <div className="chat-samples">
          {SAMPLE_QUESTIONS.map((q) => (
            <button key={q} className="chip-btn" onClick={() => send(q)}>
              {q}
            </button>
          ))}
        </div>
      )}

      <div className="chat-thread">
        {messages.map((m, i) => (
          <div key={i} className={`chat-bubble-row ${m.role}`}>
            <div className="chat-bubble">
              <p>{m.content}</p>
              {m.role === "assistant" && m.sources && m.sources.length > 0 && (
                <div className="chat-sources">
                  <button className="chip-btn chip-btn-small" onClick={() => toggleSources(i)}>
                    📚 참고한 매뉴얼 내용 {openSources.has(i) ? "숨기기" : "보기"}
                  </button>
                  {openSources.has(i) && (
                    <div className="source-list">
                      {m.sources.map((s, si) => (
                        <div key={si} className="source-item">
                          <div className="source-label">출처 {si + 1}</div>
                          <pre>{s}</pre>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          </div>
        ))}
        {sending && (
          <div className="chat-bubble-row assistant">
            <div className="chat-bubble chat-bubble-loading">매뉴얼을 검토하는 중입니다...</div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {error && <p className="form-error">{error}</p>}

      <form
        className="chat-input-row"
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="궁금한 내용을 입력하세요 (예: 평가 주기는 어떻게 되나요?)"
        />
        <button type="submit" className="btn btn-primary" disabled={sending || !input.trim()}>
          전송
        </button>
      </form>
    </div>
  );
}
