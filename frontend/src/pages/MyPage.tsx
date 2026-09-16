import * as React from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Case, Category, User } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { StatusBadge } from "../components/StatusBadge";

function NicknameEditor() {
  const { user, setUser } = useAuth();
  const [nickname, setNickname] = React.useState(user?.nickname ?? "");
  const [saving, setSaving] = React.useState(false);
  const [saved, setSaved] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function save() {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await api.put<User>("/users/me/nickname", { nickname: nickname.trim() || null });
      setUser(updated);
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "별명 저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card">
      <h2 className="section-title-sm">별명</h2>
      <p className="page-sub">기관담당자에게 이름 대신 이 별명이 보여집니다.</p>
      <div className="nickname-row">
        <input
          value={nickname}
          onChange={(e) => {
            setNickname(e.target.value);
            setSaved(false);
          }}
          maxLength={30}
          placeholder="예: 친절한 상담사"
        />
        <button className="btn btn-primary btn-small" onClick={save} disabled={saving}>
          {saving ? "저장 중..." : "저장"}
        </button>
      </div>
      {saved && <span className="saved-hint">저장됐습니다</span>}
      {error && <p className="form-error">{error}</p>}
    </div>
  );
}

function ExpertiseEditor() {
  const [all, setAll] = React.useState<Category[]>([]);
  const [selected, setSelected] = React.useState<Set<number>>(new Set());
  const [saving, setSaving] = React.useState(false);
  const [saved, setSaved] = React.useState(false);

  React.useEffect(() => {
    Promise.all([api.get<Category[]>("/categories"), api.get<Category[]>("/users/me/categories")]).then(
      ([allCats, mine]) => {
        setAll(allCats);
        setSelected(new Set(mine.map((c) => c.id)));
      }
    );
  }, []);

  function toggle(id: number) {
    setSaved(false);
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  async function save() {
    setSaving(true);
    try {
      await api.put("/users/me/categories", { category_ids: Array.from(selected) });
      setSaved(true);
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card">
      <h2 className="section-title-sm">전문분야</h2>
      <p className="page-sub">등록한 분야의 케이스만 매칭 요청 대상으로 노출됩니다.</p>
      <div className="expertise-chips">
        {all.map((c) => (
          <button
            key={c.id}
            type="button"
            className={selected.has(c.id) ? "expertise-chip active" : "expertise-chip"}
            onClick={() => toggle(c.id)}
          >
            {c.name}
          </button>
        ))}
      </div>
      <button className="btn btn-primary btn-small" onClick={save} disabled={saving}>
        {saving ? "저장 중..." : "저장"}
      </button>
      {saved && <span className="saved-hint">저장됐습니다</span>}
    </div>
  );
}

function SolutionRegisterForm({ caseId, onDone }: { caseId: number; onDone: () => void }) {
  const [open, setOpen] = React.useState(false);
  const [title, setTitle] = React.useState("");
  const [content, setContent] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  if (!open) {
    return (
      <button className="btn btn-ghost btn-small" onClick={() => setOpen(true)}>
        사례로 등록
      </button>
    );
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await api.post(`/cases/${caseId}/solutions`, { title, content });
      setOpen(false);
      onDone();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "사례 등록에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={submit} className="stack-form solution-form">
      <label htmlFor={`sol-title-${caseId}`}>사례 제목</label>
      <input id={`sol-title-${caseId}`} value={title} onChange={(e) => setTitle(e.target.value)} required />
      <label htmlFor={`sol-content-${caseId}`}>해결 내용</label>
      <textarea
        id={`sol-content-${caseId}`}
        rows={4}
        value={content}
        onChange={(e) => setContent(e.target.value)}
        required
      />
      {error && <p className="form-error">{error}</p>}
      <div className="session-actions">
        <button type="button" className="btn btn-ghost btn-small" onClick={() => setOpen(false)}>
          취소
        </button>
        <button type="submit" className="btn btn-primary btn-small" disabled={submitting}>
          {submitting ? "등록 중..." : "등록(승인 대기)"}
        </button>
      </div>
    </form>
  );
}

export function MyPage() {
  const { user } = useAuth();
  const [cases, setCases] = React.useState<Case[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [busyMatchId, setBusyMatchId] = React.useState<number | null>(null);

  const load = React.useCallback(() => {
    api.get<Case[]>("/cases").then(setCases).catch(() => {});
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  async function deleteMatchRequest(matchId: number) {
    if (!window.confirm("매칭 요청을 삭제할까요? 케이스는 다시 매칭 요청 가능한 상태로 돌아갑니다.")) return;
    setError(null);
    setBusyMatchId(matchId);
    try {
      await api.del(`/matches/${matchId}`);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "매칭 요청 삭제에 실패했습니다.");
    } finally {
      setBusyMatchId(null);
    }
  }

  return (
    <div className="page">
      <h1>마이페이지</h1>
      <p className="page-sub">
        {user?.org_name ? `${user.org_name} · ` : ""}
        {user?.name}님의 케이스·활동 이력
      </p>

      {user?.role === "expert" && (
        <>
          <NicknameEditor />
          <ExpertiseEditor />
        </>
      )}

      <h2 className="section-title">케이스 이력</h2>
      {error && <p className="form-error">{error}</p>}
      {!cases && <p className="page-loading">불러오는 중...</p>}
      {cases && cases.length === 0 && <p className="empty-state">등록된 케이스가 없습니다.</p>}

      <ul className="case-list">
        {cases?.map((c) => (
          <li key={c.id}>
            <div className="case-row">
              <Link to={`/cases/${c.id}`}>
                <div className="case-title">{c.title}</div>
                <div className="case-meta">
                  {c.category.name} · {new Date(c.created_at).toLocaleDateString("ko-KR")}
                </div>
              </Link>
              <div className="case-row-actions">
                <StatusBadge status={c.status} />
                {user?.role === "staff" && c.status === "매칭요청" && c.active_match_id && (
                  <button
                    className="btn btn-ghost btn-small"
                    onClick={() => deleteMatchRequest(c.active_match_id!)}
                    disabled={busyMatchId === c.active_match_id}
                  >
                    {busyMatchId === c.active_match_id ? "삭제 중..." : "매칭요청 삭제"}
                  </button>
                )}
                {user?.role === "expert" && c.status === "해결" && (
                  c.has_solution ? (
                    <span className="solution-registered-hint">사례 등록됨</span>
                  ) : (
                    <SolutionRegisterForm caseId={c.id} onDone={load} />
                  )
                )}
              </div>
            </div>
          </li>
        ))}
      </ul>
    </div>
  );
}
