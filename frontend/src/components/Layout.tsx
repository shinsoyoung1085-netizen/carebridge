import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { CarebridgeLogo } from "./CarebridgeLogo";

export function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  if (!user) return <Outlet />;

  return (
    <div className="app-shell">
      <header className="topbar">
        <NavLink to="/dashboard" className="brand">
          <CarebridgeLogo className="brand-logo" />
        </NavLink>
        <nav className="topnav">
          <NavLink to="/dashboard" className="nav-link">
            대시보드
          </NavLink>
          {user.role === "expert" && (
            <NavLink to="/matches" className="nav-link">
              매칭 요청함
            </NavLink>
          )}
          <NavLink to="/solutions" className="nav-link">
            사례 아카이브
          </NavLink>
          <NavLink to="/mypage" className="nav-link">
            마이페이지
          </NavLink>
          {user.role === "admin" && (
            <NavLink to="/admin" className="nav-link">
              관리자
            </NavLink>
          )}
          <NavLink to="/manual" className="nav-link">
            편하게 물어보세요
          </NavLink>
        </nav>
        <div className="user-badge">
          <span className="user-name">
            {user.org_name ? `${user.org_name}, ` : ""}
            {user.name}님
          </span>
          <span className={`role-pill role-${user.role}`}>
            {user.role === "staff" ? "기관담당자" : user.role === "expert" ? "숙련자" : "관리자"}
          </span>
          <button
            className="btn btn-ghost"
            onClick={() => {
              logout();
              navigate("/login");
            }}
          >
            로그아웃
          </button>
        </div>
      </header>
      <main className="content">
        <Outlet />
      </main>
    </div>
  );
}
