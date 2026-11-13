import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api } from "../services/api";
import type { User } from "../types";

type AuthState = {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (payload: { email: string; password: string; full_name: string; phone?: string }) => Promise<void>;
  logout: () => void;
};

const Ctx = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const access = localStorage.getItem("sn_access");
    if (!access) {
      setLoading(false);
      return;
    }
    api
      .get<User>("/api/auth/me")
      .then(setUser)
      .catch(() => {
        localStorage.removeItem("sn_access");
        localStorage.removeItem("sn_refresh");
      })
      .finally(() => setLoading(false));
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      loading,
      async login(email, password) {
        const tokens = await api.post<{ access_token: string; refresh_token: string }>("/api/auth/login", { email, password });
        localStorage.setItem("sn_access", tokens.access_token);
        localStorage.setItem("sn_refresh", tokens.refresh_token);
        setUser(await api.get<User>("/api/auth/me"));
      },
      async register(payload) {
        await api.post("/api/auth/register", payload);
        const tokens = await api.post<{ access_token: string; refresh_token: string }>("/api/auth/login", {
          email: payload.email,
          password: payload.password,
        });
        localStorage.setItem("sn_access", tokens.access_token);
        localStorage.setItem("sn_refresh", tokens.refresh_token);
        setUser(await api.get<User>("/api/auth/me"));
      },
      logout() {
        localStorage.removeItem("sn_access");
        localStorage.removeItem("sn_refresh");
        setUser(null);
      },
    }),
    [user, loading],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useAuth() {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error("AuthProvider missing");
  return ctx;
}
