import * as React from "react";
import { Link } from "react-router-dom";
import { api, ApiError } from "../api/client";
import type { Case, Category, User } from "../api/types";
import { useAuth } from "../context/AuthContext";
import { StatusBadge } from "../components/StatusBadge";

function NameEditor() {
  const { user, setUser } = useAuth();
  const [name, setName] = React.useState(user?.name ?? "");
  const [saving, setSaving] = React.useState(false);
  const [saved, setSaved] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await api.put<User>("/users/me/name", { name: name.trim() });
      setUser(updated);
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "이름 저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={save}>
      <label htmlFor="account-name">이름</label>
      <div className="nickname-row">
        <input
          id="account-name"
          value={name}
          onChange={(e) => {
            setName(e.target.value);
            setSaved(false);
          }}
          maxLength={50}
          required
        />
        <button type="submit" className="btn btn-primary btn-small" disabled={saving || !name.trim()}>
          {saving ? "저장 중..." : "저장"}
        </button>
      </div>
      {saved && <span className="saved-hint">저장됐습니다</span>}
      {error && <p className="form-error">{error}</p>}
    </form>
  );
}

function EmailEditor() {
  const { user, setUser } = useAuth();
  const [email, setEmail] = React.useState(user?.email ?? "");
  const [password, setPassword] = React.useState("");
  const [saving, setSaving] = React.useState(false);
  const [saved, setSaved] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await api.put<User>("/users/me/email", {
        email: email.trim(),
        current_password: password,
      });
      setUser(updated);
      setPassword("");
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "이메일 변경에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={save} className="stack-form">
      <label htmlFor="account-email">이메일 (로그인 아이디)</label>
      <input
        id="account-email"
        type="email"
        value={email}
        onChange={(e) => {
          setEmail(e.target.value);
          setSaved(false);
        }}
        required
      />
      <label htmlFor="account-email-password">현재 비밀번호</label>
      <input
        id="account-email-password"
        type="password"
        autoComplete="current-password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        required
      />
      {error && <p className="form-error">{error}</p>}
      <div>
        <button type="submit" className="btn btn-primary btn-small" disabled={saving || email.trim() === user?.email}>
          {saving ? "변경 중..." : "이메일 변경"}
        </button>
        {saved && <span className="saved-hint">변경됐습니다. 다음 로그인부터 새 이메일을 사용하세요.</span>}
      </div>
    </form>
  );
}

function PasswordEditor() {
  const [current, setCurrent] = React.useState("");
  const [next, setNext] = React.useState("");
  const [confirm, setConfirm] = React.useState("");
  const [saving, setSaving] = React.useState(false);
  const [saved, setSaved] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function save(e: React.FormEvent) {
    e.preventDefault();
    setSaved(false);
    setError(null);
    if (next.length < 8) {
      setError("새 비밀번호는 8자 이상이어야 합니다.");
      return;
    }
    if (next !== confirm) {
      setError("새 비밀번호가 서로 일치하지 않습니다.");
      return;
    }
    setSaving(true);
    try {
      await api.put("/users/me/password", { current_password: current, new_password: next });
      setCurrent("");
      setNext("");
      setConfirm("");
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "비밀번호 변경에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form onSubmit={save} className="stack-form">
      <label htmlFor="account-current-password">현재 비밀번호</label>
      <input
        id="account-current-password"
        type="password"
        autoComplete="current-password"
        value={current}
        onChange={(e) => setCurrent(e.target.value)}
        required
      />
      <label htmlFor="account-new-password">새 비밀번호 (8자 이상)</label>
      <input
        id="account-new-password"
        type="password"
        autoComplete="new-password"
        value={next}
        onChange={(e) => setNext(e.target.value)}
        minLength={8}
        maxLength={100}
        required
      />
      <label htmlFor="account-confirm-password">새 비밀번호 확인</label>
      <input
        id="account-confirm-password"
        type="password"
        autoComplete="new-password"
        value={confirm}
        onChange={(e) => setConfirm(e.target.value)}
        required
      />
      {error && <p className="form-error">{error}</p>}
      <div>
        <button type="submit" className="btn btn-primary btn-small" disabled={saving}>
          {saving ? "변경 중..." : "비밀번호 변경"}
        </button>
        {saved && <span className="saved-hint">변경됐습니다</span>}
      </div>
    </form>
  );
}

function AccountEditor() {
  return (
    <div className="card">
      <h2 className="section-title-sm">계정 정보</h2>
      <NameEditor />
      <EmailEditor />
      <PasswordEditor />
    </div>
  );
}

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

function OrgNameEditor() {
  const { user, setUser } = useAuth();
  const [orgName, setOrgName] = React.useState(user?.org_name ?? "");
  const [saving, setSaving] = React.useState(false);
  const [saved, setSaved] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  async function save() {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const updated = await api.put<User>("/users/me/org-name", { org_name: orgName.trim() || null });
      setUser(updated);
      setSaved(true);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "소속 기관 저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="card">
      <h2 className="section-title-sm">소속 기관</h2>
      <p className="page-sub">상단바와 프로필에 표시되는 소속 기관명이에요.</p>
      <div className="nickname-row">
        <input
          value={orgName}
          onChange={(e) => {
            setOrgName(e.target.value);
            setSaved(false);
          }}
          maxLength={100}
          placeholder="예: 햇살요양원"
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

function SolutionRegisterForm({
  caseId,
  caseTitle,
  initialContent,
  onDone,
}: {
  caseId: number;
  caseTitle: string;
  initialContent: string;
  onDone: () => void;
}) {
  const [open, setOpen] = React.useState(false);
  const [title, setTitle] = React.useState(caseTitle);
  const [content, setContent] = React.useState(initialContent);
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
      <p className="hint-text-sm">케이스 제목과 상담 메모(해결 내용)를 불러왔어요. 필요한 대로 고쳐서 등록하세요.</p>
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

function CaseRow({
  c,
  user,
  busyMatchId,
  busyDeleteCaseId,
  onDeleteMatch,
  onDeleteCase,
  onSolutionDone,
}: {
  c: Case;
  user: { role: string } | null;
  busyMatchId: number | null;
  busyDeleteCaseId: number | null;
  onDeleteMatch: (matchId: number) => void;
  onDeleteCase: (caseId: number) => void;
  onSolutionDone: () => void;
}) {
  return (
    <li>
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
              onClick={() => onDeleteMatch(c.active_match_id!)}
              disabled={busyMatchId === c.active_match_id}
            >
              {busyMatchId === c.active_match_id ? "삭제 중..." : "매칭요청 삭제"}
            </button>
          )}
          {user?.role === "staff" && (
            <button
              className="btn btn-ghost btn-small btn-danger"
              onClick={() => onDeleteCase(c.id)}
              disabled={busyDeleteCaseId === c.id}
            >
              {busyDeleteCaseId === c.id ? "삭제 중..." : "케이스 삭제"}
            </button>
          )}
          {user?.role === "expert" && c.status === "해결" && (
            c.has_solution ? (
              <span className="solution-registered-hint">사례 등록됨</span>
            ) : (
              <SolutionRegisterForm
                caseId={c.id}
                caseTitle={c.title}
                initialContent={c.session_memo ?? c.description}
                onDone={onSolutionDone}
              />
            )
          )}
        </div>
      </div>
    </li>
  );
}

export function MyPage() {
  const { user } = useAuth();
  const [cases, setCases] = React.useState<Case[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [busyMatchId, setBusyMatchId] = React.useState<number | null>(null);
  const [busyDeleteCaseId, setBusyDeleteCaseId] = React.useState<number | null>(null);

  const load = React.useCallback(() => {
    api.get<Case[]>("/cases").then(setCases).catch(() => {});
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  const pendingMatchCases = React.useMemo(
    () => (user?.role === "staff" ? (cases ?? []).filter((c) => c.status === "매칭요청") : []),
    [cases, user]
  );
  const inProgressCases = React.useMemo(
    () => (cases ?? []).filter((c) => c.status === "상담중"),
    [cases]
  );
  const otherCases = React.useMemo(
    () => (cases ?? []).filter((c) => !pendingMatchCases.includes(c) && !inProgressCases.includes(c)),
    [cases, pendingMatchCases, inProgressCases]
  );

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

  async function deleteCase(caseId: number) {
    if (
      !window.confirm(
        "케이스를 완전히 삭제할까요? 매칭·상담 기록까지 전부 삭제되고 되돌릴 수 없습니다."
      )
    )
      return;
    setError(null);
    setBusyDeleteCaseId(caseId);
    try {
      await api.del(`/cases/${caseId}`);
      load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "케이스 삭제에 실패했습니다.");
    } finally {
      setBusyDeleteCaseId(null);
    }
  }

  return (
    <div className="page">
      <h1>마이페이지</h1>
      <p className="page-sub">
        {user?.org_name ? `${user.org_name} · ` : ""}
        {user?.name}님의 케이스·활동 이력
      </p>

      <AccountEditor />

      {user?.role === "staff" && <OrgNameEditor />}

      {user?.role === "expert" && (
        <>
          <NicknameEditor />
          <ExpertiseEditor />
        </>
      )}

      {error && <p className="form-error">{error}</p>}
      {!cases && <p className="page-loading">불러오는 중...</p>}
      {cases && cases.length === 0 && <p className="empty-state">등록된 케이스가 없습니다.</p>}

      {user?.role === "staff" && pendingMatchCases.length > 0 && (
        <>
          <h2 className="section-title">매칭 요청 중</h2>
          <ul className="case-list">
            {pendingMatchCases.map((c) => (
              <CaseRow
                key={c.id}
                c={c}
                user={user}
                busyMatchId={busyMatchId}
                busyDeleteCaseId={busyDeleteCaseId}
                onDeleteMatch={deleteMatchRequest}
                onDeleteCase={deleteCase}
                onSolutionDone={load}
              />
            ))}
          </ul>
        </>
      )}

      {inProgressCases.length > 0 && (
        <>
          <h2 className="section-title">상담 진행 중</h2>
          <ul className="case-list">
            {inProgressCases.map((c) => (
              <CaseRow
                key={c.id}
                c={c}
                user={user}
                busyMatchId={busyMatchId}
                busyDeleteCaseId={busyDeleteCaseId}
                onDeleteMatch={deleteMatchRequest}
                onDeleteCase={deleteCase}
                onSolutionDone={load}
              />
            ))}
          </ul>
        </>
      )}

      <h2 className="section-title">케이스 이력</h2>
      <ul className="case-list">
        {otherCases.map((c) => (
          <CaseRow
            key={c.id}
            c={c}
            user={user}
            busyMatchId={busyMatchId}
            busyDeleteCaseId={busyDeleteCaseId}
            onDeleteMatch={deleteMatchRequest}
            onDeleteCase={deleteCase}
            onSolutionDone={load}
          />
        ))}
      </ul>
    </div>
  );
}
