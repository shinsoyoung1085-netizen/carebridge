import * as React from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Match } from "../api/types";
import { StatusBadge } from "../components/StatusBadge";
import { Tooltip } from "../components/Tooltip";

export function MatchesPage() {
  const [matches, setMatches] = React.useState<Match[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [busyId, setBusyId] = React.useState<number | null>(null);

  const load = React.useCallback(() => {
    api.get<Match[]>("/matches").then(setMatches).catch(() => setError("매칭 요청함을 불러오지 못했습니다."));
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  async function decide(matchId: number, action: "accept" | "reject") {
    setError(null);
    setBusyId(matchId);
    try {
      await api.put<Match>(`/matches/${matchId}`, { action });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "처리에 실패했습니다.");
    } finally {
      setBusyId(null);
    }
  }

  const pending = matches?.filter((m) => m.status === "요청") ?? [];
  const handled = matches?.filter((m) => m.status !== "요청") ?? [];

  return (
    <div className="page">
      <h1>매칭 요청함</h1>
      <p className="page-sub">기관담당자로부터 들어온 매칭 요청입니다.</p>
      <p className="hint-text">💡 케이스 제목에 마우스를 올리면 요청 상세 내용을 볼 수 있어요.</p>

      {error && <p className="form-error">{error}</p>}
      {!matches && <p className="page-loading">불러오는 중...</p>}
      {matches && pending.length === 0 && <p className="empty-state">대기 중인 요청이 없습니다.</p>}

      <ul className="match-list">
        {pending.map((m) => (
          <li key={m.id} className="match-row match-row-card">
            <div>
              <div className="case-title">
                <Tooltip text={m.case_description}>{m.case_title}</Tooltip>
              </div>
              <div className="case-meta">{new Date(m.requested_at).toLocaleString("ko-KR")}</div>
            </div>
            <div className="match-actions">
              <button className="btn btn-ghost" disabled={busyId === m.id} onClick={() => decide(m.id, "reject")}>
                거절
              </button>
              <button className="btn btn-primary" disabled={busyId === m.id} onClick={() => decide(m.id, "accept")}>
                수락
              </button>
            </div>
          </li>
        ))}
      </ul>

      {handled.length > 0 && (
        <>
          <h2 className="section-title">처리한 요청</h2>
          <ul className="match-list">
            {handled.map((m) => (
              <li key={m.id} className="match-row">
                <Tooltip text={m.case_description}>
                  <span>{m.case_title}</span>
                </Tooltip>
                <StatusBadge status={m.status} />
                {m.session_id && (
                  <Link to={`/sessions/${m.session_id}`} className="btn btn-small">
                    상담 세션으로 이동
                  </Link>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
