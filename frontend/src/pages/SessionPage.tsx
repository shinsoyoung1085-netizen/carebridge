import * as React from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { ConsultSession, Review } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { StatusBadge } from "../components/StatusBadge";
import { StarRating } from "../components/StarRating";

const REMOTE_TOOLS = ["이지헬프", "헬프컴", "구글원격", "기타"];

export function SessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { user } = useAuth();

  const [session, setSession] = React.useState<ConsultSession | null>(null);
  const [remoteTool, setRemoteTool] = React.useState("");
  const [accessCode, setAccessCode] = React.useState("");
  const [memo, setMemo] = React.useState("");
  const [rating, setRating] = React.useState(5);
  const [comment, setComment] = React.useState("");
  const [review, setReview] = React.useState<Review | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [busy, setBusy] = React.useState(false);

  const load = React.useCallback(() => {
    if (!sessionId) return;
    api
      .get<ConsultSession>(`/sessions/${sessionId}`)
      .then((s) => {
        setSession(s);
        setRemoteTool(s.remote_tool ?? "");
        setAccessCode(s.access_code ?? "");
        setMemo(s.memo ?? "");
      })
      .catch(() => setError("세션을 불러오지 못했습니다."));
  }, [sessionId]);

  React.useEffect(() => {
    load();
  }, [load]);

  if (!session || !user) {
    return <div className="page">{error ?? "불러오는 중..."}</div>;
  }

  const isExpert = user.id === session.expert_id;
  const isRequester = user.id === session.requester_id;

  async function saveMemo() {
    if (!sessionId) return;
    setError(null);
    setBusy(true);
    try {
      const updated = await api.put<ConsultSession>(`/sessions/${sessionId}`, { memo });
      setSession(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "메모 저장에 실패했습니다.");
    } finally {
      setBusy(false);
    }
  }

  async function startSession() {
    if (!sessionId) return;
    setError(null);
    setBusy(true);
    try {
      const updated = await api.put<ConsultSession>(`/sessions/${sessionId}`, {
        remote_tool: remoteTool,
        access_code: accessCode,
        status: "진행중",
      });
      setSession(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "세션 시작에 실패했습니다.");
    } finally {
      setBusy(false);
    }
  }

  async function endSession() {
    if (!sessionId) return;
    setError(null);
    setBusy(true);
    try {
      const updated = await api.put<ConsultSession>(`/sessions/${sessionId}`, { memo, status: "완료" });
      setSession(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "세션 종료에 실패했습니다.");
    } finally {
      setBusy(false);
    }
  }

  async function submitReview(e: React.FormEvent) {
    e.preventDefault();
    if (!sessionId) return;
    setError(null);
    setBusy(true);
    try {
      const created = await api.post<Review>(`/sessions/${sessionId}/reviews`, { rating, comment });
      setReview(created);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "평가 등록에 실패했습니다.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="page page-narrow">
      <Link to={`/cases/${session.case_id}`} className="back-link">
        ← 케이스로
      </Link>

      <div className="case-header">
        <StatusBadge status={session.status} />
      </div>
      <h1>상담 세션</h1>

      <div className="card">
        <h2 className="section-title-sm">원격지원 연결</h2>

        <label htmlFor="remote-tool">원격지원 도구</label>
        <select
          id="remote-tool"
          value={remoteTool}
          onChange={(e) => setRemoteTool(e.target.value)}
          disabled={!isExpert || session.status !== "대기"}
        >
          <option value="">선택해주세요</option>
          {REMOTE_TOOLS.map((t) => (
            <option key={t} value={t}>
              {t}
            </option>
          ))}
        </select>

        <label htmlFor="access-code">접속코드</label>
        <input
          id="access-code"
          value={accessCode}
          onChange={(e) => setAccessCode(e.target.value)}
          placeholder={isExpert ? "발급받은 접속코드를 입력하세요" : "숙련자가 발급 예정입니다"}
          disabled={!isExpert || session.status !== "대기"}
        />

        <label htmlFor="session-memo">상담 메모</label>
        <textarea
          id="session-memo"
          rows={5}
          value={memo}
          onChange={(e) => setMemo(e.target.value)}
          placeholder="상담 중 메모를 남겨주세요"
          disabled={session.status === "완료"}
        />
        {session.status !== "완료" && (
          <button className="btn btn-ghost btn-small" onClick={saveMemo} disabled={busy}>
            메모 저장
          </button>
        )}

        {error && <p className="form-error">{error}</p>}

        <div className="session-actions">
          {isExpert && session.status === "대기" && (
            <button className="btn btn-primary" onClick={startSession} disabled={busy || !remoteTool || !accessCode}>
              세션 시작
            </button>
          )}
          {isExpert && session.status === "진행중" && (
            <button className="btn btn-primary" onClick={endSession} disabled={busy}>
              세션 종료
            </button>
          )}
        </div>
      </div>

      {isRequester && session.status === "완료" && (
        <div className="card">
          <h2 className="section-title-sm">세션 평가</h2>
          {review ? (
            <p className="empty-state">평가를 등록했습니다. 평점 {review.rating}점 — 감사합니다!</p>
          ) : (
            <form onSubmit={submitReview} className="stack-form">
              <label>평점</label>
              <StarRating value={rating} onChange={setRating} disabled={busy} />
              <label htmlFor="review-comment">코멘트</label>
              <textarea id="review-comment" rows={3} value={comment} onChange={(e) => setComment(e.target.value)} />
              <button type="submit" className="btn btn-primary" disabled={busy}>
                평가 등록
              </button>
            </form>
          )}
        </div>
      )}
    </div>
  );
}
