import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export function RequireAuth() {
  const { user, loading } = useAuth();

  if (loading) return <div className="page-loading">불러오는 중...</div>;
  if (!user) return <Navigate to="/login" replace />;

  return <Outlet />;
}
