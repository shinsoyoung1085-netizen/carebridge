import * as React from "react";
import { Link, useParams } from "react-router-dom";
import { api, ApiError, resolveFileUrl } from "../api/client";
import type { Case, Expert, Match } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { StatusBadge } from "../components/StatusBadge";
import { TemperatureBadge } from "../components/TemperatureBadge";

export function CaseDetailPage() {
  const { caseId } = useParams<{ caseId: string }>();
  const { user } = useAuth();

  const [caseData, setCaseData] = React.useState<Case | null>(null);
  const [matches, setMatches] = React.useState<Match[]>([]);
  const [experts, setExperts] = React.useState<Expert[]>([]);
  const [selectedExpert, setSelectedExpert] = React.useState<number | "">("");
  const [error, setError] = React.useState<string | null>(null);
  const [requesting, setRequesting] = React.useState(false);

  const load = React.useCallback(() => {
    if (!caseId) return;
    api.get<Case>(`/cases/${caseId}`).then(setCaseData).catch(() => setError("케이스를 불러오지 못했습니다."));
    api.get<Match[]>(`/cases/${caseId}/matches`).then(setMatches).catch(() => {});
  }, [caseId]);

  React.useEffect(() => {
    load();
  }, [load]);

  React.useEffect(() => {
    if (user?.role === "staff" && caseData) {
      api
        .get<Expert[]>(`/experts?category_id=${caseData.category.id}`)
        .then(setExperts)
        .catch(() => {});
    }
  }, [user, caseData]);

  const activeMatch = matches.find((m) => m.status === "요청" || m.status === "수락");

  async function requestMatch() {
    if (!caseId || !selectedExpert) return;
    setError(null);
    setRequesting(true);
    try {
      await api.post<Match>(`/cases/${caseId}/matches`, { expert_id: selectedExpert });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "매칭 요청에 실패했습니다.");
    } finally {
      setRequesting(false);
    }
  }

  if (!caseData) {
    return <div className="page">{error ?? "불러오는 중..."}</div>;
  }

  return (
    <div className="page page-narrow">
      <Link to="/dashboard" className="back-link">
        ← 대시보드로
      </Link>

      <div className="case-header">
        <StatusBadge status={caseData.status} />
        <span className="case-meta">
          {caseData.category.name} · {new Date(caseData.created_at).toLocaleDateString("ko-KR")}
        </span>
      </div>
      <h1>{caseData.title}</h1>
      <p className="case-description">{caseData.description}</p>

      {caseData.attachments.length > 0 && (
        <div className="photo-gallery">
          {caseData.attachments.map((a) => (
            <a key={a.id} href={resolveFileUrl(a.file_url)} target="_blank" rel="noreferrer" className="gallery-item">
              <img src={resolveFileUrl(a.file_url)} alt={a.file_name} />
            </a>
          ))}
        </div>
      )}

      <div className="card">
        <h2 className="section-title-sm">매칭 현황</h2>

        {matches.length === 0 && <p className="empty-state">아직 매칭 요청이 없습니다.</p>}

        <ul className="match-list">
          {matches.map((m) => (
            <li key={m.id} className="match-row">
              <span>{m.expert_display_name}</span>
              <StatusBadge status={m.status} />
              {m.session_id && (
                <Link to={`/sessions/${m.session_id}`} className="btn btn-small">
                  상담 세션으로 이동
                </Link>
              )}
            </li>
          ))}
        </ul>

        {user?.role === "staff" && user.id === caseData.requester_id && !activeMatch && (
          <div className="match-request-form">
            {experts.length === 0 ? (
              <p className="empty-state">
                "{caseData.category.name}" 분야를 전문분야로 등록한 숙련자가 아직 없습니다.
              </p>
            ) : (
              <>
                <div className="expert-picker">
                  {experts.map((e) => (
                    <button
                      key={e.id}
                      type="button"
                      className={selectedExpert === e.id ? "expert-card selected" : "expert-card"}
                      onClick={() => setSelectedExpert(e.id)}
                    >
                      <span className="expert-name">{e.nickname || e.name}</span>
                      <TemperatureBadge value={e.temperature} />
                      <span className="expert-meta">리뷰 {e.review_count}건</span>
                    </button>
                  ))}
                </div>
                <button className="btn btn-primary" onClick={requestMatch} disabled={!selectedExpert || requesting}>
                  {requesting ? "요청 중..." : "숙련자 매칭 요청"}
                </button>
              </>
            )}
          </div>
        )}

        {error && <p className="form-error">{error}</p>}
      </div>
    </div>
  );
}
