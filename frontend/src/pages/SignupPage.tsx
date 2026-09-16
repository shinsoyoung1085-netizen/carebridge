import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../api/client";
import { CarebridgeLogo } from "../components/CarebridgeLogo";
import type { UserRole } from "../api/types";

export function SignupPage() {
  const { signup } = useAuth();
  const navigate = useNavigate();
  const [name, setName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [role, setRole] = React.useState<UserRole>("staff");
  const [orgName, setOrgName] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await signup({
        name,
        email,
        password,
        role,
        org_name: role === "staff" ? orgName : undefined,
      });
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "회원가입에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <CarebridgeLogo className="auth-logo" />

        <div className="role-toggle">
          <button
            type="button"
            className={role === "staff" ? "role-option active" : "role-option"}
            onClick={() => setRole("staff")}
          >
            기관담당자
          </button>
          <button
            type="button"
            className={role === "expert" ? "role-option active" : "role-option"}
            onClick={() => setRole("expert")}
          >
            숙련자
          </button>
        </div>

        <form onSubmit={handleSubmit} className="auth-form">
          <label htmlFor="signup-name">이름</label>
          <input id="signup-name" value={name} onChange={(e) => setName(e.target.value)} required />

          <label htmlFor="signup-email">이메일</label>
          <input
            id="signup-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label htmlFor="signup-password">비밀번호</label>
          <input
            id="signup-password"
            type="password"
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {role === "staff" && (
            <>
              <label htmlFor="signup-org">소속 기관</label>
              <input
                id="signup-org"
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                placeholder="예: 햇살요양원"
              />
            </>
          )}

          {error && <p className="form-error">{error}</p>}

          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "가입 중..." : "회원가입"}
          </button>
        </form>

        <p className="auth-switch">
          이미 계정이 있으신가요? <Link to="/login">로그인</Link>
        </p>
      </div>
    </div>
  );
}
