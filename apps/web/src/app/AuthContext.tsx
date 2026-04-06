import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { fetchMe, login as loginRequest, type AuthResponse, type AuthUser, type Membership } from "../lib/api";

type SessionState = {
  user: AuthUser | null;
  memberships: Membership[];
  accessToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const STORAGE_KEY = "gra_session";

const AuthContext = createContext<SessionState | undefined>(undefined);

type PersistedSession = {
  accessToken: string;
  refreshToken: string;
  user: AuthUser;
  memberships: Membership[];
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [memberships, setMemberships] = useState<Membership[]>([]);
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      setLoading(false);
      return;
    }

    const session = JSON.parse(raw) as PersistedSession;
    setAccessToken(session.accessToken);
    setUser(session.user);
    setMemberships(session.memberships);

    fetchMe(session.accessToken)
      .then((result) => {
        setUser(result.user);
        setMemberships(result.memberships);
      })
      .catch(() => {
        localStorage.removeItem(STORAGE_KEY);
        setAccessToken(null);
        setUser(null);
        setMemberships([]);
      })
      .finally(() => setLoading(false));
  }, []);

  async function login(email: string, password: string) {
    const response: AuthResponse = await loginRequest({ email, password });
    const persisted: PersistedSession = {
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
      user: response.user,
      memberships: response.memberships,
    };

    localStorage.setItem(STORAGE_KEY, JSON.stringify(persisted));
    setAccessToken(response.access_token);
    setUser(response.user);
    setMemberships(response.memberships);
  }

  function logout() {
    localStorage.removeItem(STORAGE_KEY);
    setAccessToken(null);
    setUser(null);
    setMemberships([]);
  }

  const value = useMemo(
    () => ({
      user,
      memberships,
      accessToken,
      loading,
      login,
      logout,
    }),
    [user, memberships, accessToken, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
