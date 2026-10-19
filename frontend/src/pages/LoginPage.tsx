import * as React from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ApiError } from "../api/client";
import { CarebridgeLogo } from "../components/CarebridgeLogo";

export function LoginPage() {
  const { login, guestLogin } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [error, setError] = React.useState<string | null>(null);
  const [submitting, setSubmitting] = React.useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "로그인에 실패했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleGuest(role: "staff" | "expert") {
    setError(null);
    setSubmitting(true);
    try {
      await guestLogin(role);
      navigate("/dashboard");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "체험 계정으로 입장하지 못했습니다.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <CarebridgeLogo className="auth-logo" />
        <p className="auth-tagline">장기요양기관 실무자를 위한 원격 업무지원 매칭 플랫폼</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <label htmlFor="login-email">이메일</label>
          <input
            id="login-email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />

          <label htmlFor="login-password">비밀번호</label>
          <input
            id="login-password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />

          {error && <p className="form-error">{error}</p>}

          <button type="submit" className="btn btn-primary" disabled={submitting}>
            {submitting ? "로그인 중..." : "로그인"}
          </button>
        </form>

        <p className="auth-switch">
          계정이 없으신가요? <Link to="/signup">회원가입</Link>
        </p>

        <div className="guest-box">
          <p className="guest-title">회원가입 없이 구경하기</p>
          <div className="guest-buttons">
            <button type="button" className="btn" disabled={submitting} onClick={() => handleGuest("staff")}>
              기관담당자로 구경
            </button>
            <button type="button" className="btn" disabled={submitting} onClick={() => handleGuest("expert")}>
              숙련자로 구경
            </button>
          </div>
          <p className="guest-note">공용 체험 계정입니다. 다른 방문자와 데이터가 함께 보일 수 있으니 개인정보는 입력하지 마세요.</p>
        </div>
      </div>
    </div>
  );
}
