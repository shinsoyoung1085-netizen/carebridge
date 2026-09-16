import * as React from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import type { Case } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { StatusBadge } from "../components/StatusBadge";

export function DashboardPage() {
  const { user } = useAuth();
  const [cases, setCases] = React.useState<Case[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  React.useEffect(() => {
    api
      .get<Case[]>("/cases")
      .then(setCases)
      .catch(() => setError("케이스 목록을 불러오지 못했습니다."));
  }, []);

  const openCount = cases?.filter((c) => c.status !== "해결").length ?? 0;

  return (
    <div className="page">
      {user?.role === "staff" && (
        <div className="page-header page-header-end">
          <Link to="/cases/new" className="btn btn-primary">
            + 새 케이스 등록
          </Link>
        </div>
      )}

      <Link to="/manual" className="chat-cta">
        <span className="chat-cta-text">숙련자 매칭 전에 편하게 먼저 물어보세요</span>
        <span className="chat-cta-arrow">바로 답변받기 →</span>
      </Link>

      <div className="stat-row">
        <div className="stat-tile">
          <span className="stat-value">{openCount}</span>
          <span className="stat-label">진행 중인 케이스</span>
        </div>
        <div className="stat-tile">
          <span className="stat-value">{(cases?.length ?? 0) - openCount}</span>
          <span className="stat-label">해결 완료</span>
        </div>
      </div>

      <h2 className="section-title">{user?.role === "expert" ? "내가 담당한 케이스" : "내 케이스"}</h2>

      {error && <p className="form-error">{error}</p>}
      {!cases && !error && <p className="page-loading">불러오는 중...</p>}
      {cases && cases.length === 0 && <p className="empty-state">등록된 케이스가 없습니다.</p>}

      <ul className="case-list">
        {cases?.map((c) => (
          <li key={c.id}>
            <Link to={`/cases/${c.id}`} className="case-row">
              <div>
                <div className="case-title">{c.title}</div>
                <div className="case-meta">
                  {c.category.name} · {new Date(c.created_at).toLocaleDateString("ko-KR")}
                </div>
              </div>
              <StatusBadge status={c.status} />
            </Link>
          </li>
        ))}
      </ul>
    </div>
  );
}
