import * as React from "react";
import { api, ApiError } from "../api/client";
import type { Solution } from "../api/types";

export function AdminDashboardPage() {
  const [pending, setPending] = React.useState<Solution[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [busyId, setBusyId] = React.useState<number | null>(null);

  const load = React.useCallback(() => {
    api
      .get<Solution[]>("/admin/solutions?is_published=false")
      .then(setPending)
      .catch(() => setError("목록을 불러오지 못했습니다."));
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  async function approve(id: number) {
    setError(null);
    setBusyId(id);
    try {
      await api.put(`/admin/solutions/${id}/publish`, { is_published: true });
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "승인에 실패했습니다.");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="page">
      <h1>관리자 대시보드</h1>
      <div className="admin-tabs">
        <span className="admin-tab active">사례 검수</span>
      </div>

      <p className="page-sub">숙련자가 등록한 해결 사례 중 승인 대기 중인 목록입니다.</p>

      {error && <p className="form-error">{error}</p>}
      {!pending && !error && <p className="page-loading">불러오는 중...</p>}
      {pending && pending.length === 0 && <p className="empty-state">검수 대기 중인 사례가 없습니다.</p>}

      <ul className="solution-list">
        {pending?.map((s) => (
          <li key={s.id} className="solution-item">
            <div className="solution-summary">
              <div>
                <div className="case-title">{s.title}</div>
                <div className="case-meta">{s.category.name}</div>
              </div>
              <button className="btn btn-primary btn-small" onClick={() => approve(s.id)} disabled={busyId === s.id}>
                {busyId === s.id ? "처리 중..." : "승인"}
              </button>
            </div>
            <p className="solution-content">{s.content}</p>
          </li>
        ))}
      </ul>
    </div>
  );
}
