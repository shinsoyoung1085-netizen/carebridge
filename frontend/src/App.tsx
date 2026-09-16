import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import { RequireAuth } from "./components/RequireAuth";
import { RequireAdmin } from "./components/RequireAdmin";
import { Layout } from "./components/Layout";
import { LoginPage } from "./pages/LoginPage";
import { SignupPage } from "./pages/SignupPage";
import { DashboardPage } from "./pages/DashboardPage";
import { NewCasePage } from "./pages/NewCasePage";
import { CaseDetailPage } from "./pages/CaseDetailPage";
import { MatchesPage } from "./pages/MatchesPage";
import { SessionPage } from "./pages/SessionPage";
import { ManualChatPage } from "./pages/ManualChatPage";
import { SolutionArchivePage } from "./pages/SolutionArchivePage";
import { MyPage } from "./pages/MyPage";
import { AdminDashboardPage } from "./pages/AdminDashboardPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/signup" element={<SignupPage />} />

          <Route element={<RequireAuth />}>
            <Route element={<Layout />}>
              <Route path="/dashboard" element={<DashboardPage />} />
              <Route path="/cases/new" element={<NewCasePage />} />
              <Route path="/cases/:caseId" element={<CaseDetailPage />} />
              <Route path="/matches" element={<MatchesPage />} />
              <Route path="/sessions/:sessionId" element={<SessionPage />} />
              <Route path="/manual" element={<ManualChatPage />} />
              <Route path="/solutions" element={<SolutionArchivePage />} />
              <Route path="/mypage" element={<MyPage />} />
              <Route element={<RequireAdmin />}>
                <Route path="/admin" element={<AdminDashboardPage />} />
              </Route>
            </Route>
          </Route>

          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
