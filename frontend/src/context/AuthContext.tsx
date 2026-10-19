import * as React from "react";
import { api, getToken, setToken } from "../api/client";
import type { User, UserRole } from "../api/types";

interface SignupInput {
  name: string;
  email: string;
  password: string;
  role: UserRole;
  org_name?: string;
}

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (input: SignupInput) => Promise<void>;
  logout: () => void;
  setUser: (user: User) => void;
}

const AuthContext = React.createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = React.useState<User | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    const token = getToken();
    if (!token) {
      setLoading(false);
      return;
    }
    api
      .get<User>("/users/me")
      .then(setUser)
      .catch(() => setToken(null))
      .finally(() => setLoading(false));
  }, []);

  const login = React.useCallback(async (email: string, password: string) => {
    const res = await api.post<{ access_token: string; user: User }>("/auth/login", {
      email,
      password,
    });
    setToken(res.access_token);
    setUser(res.user);
  }, []);

  const signup = React.useCallback(async (input: SignupInput) => {
    const res = await api.post<{ access_token: string; user: User }>("/auth/signup", input);
    setToken(res.access_token);
    setUser(res.user);
  }, []);

  const logout = React.useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider value={{ user, loading, login, signup, logout, setUser }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = React.useContext(AuthContext);
  if (!ctx) throw new Error("useAuth는 AuthProvider 내부에서만 사용할 수 있습니다.");
  return ctx;
}
