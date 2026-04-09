import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { fetchMe, login as loginRequest, type AuthUser, type Membership } from "../lib/api";
import {
  clearStoredSession,
  getStoredSession,
  saveStoredSession,
  subscribeSession,
  type PersistedSession,
} from "../lib/session";

type SessionState = {
  user: AuthUser | null;
  memberships: Membership[];
  accessToken: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
};

const AuthContext = createContext<SessionState | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => getStoredSession()?.user ?? null);
  const [memberships, setMemberships] = useState<Membership[]>(() => getStoredSession()?.memberships ?? []);
  const [accessToken, setAccessToken] = useState<string | null>(() => getStoredSession()?.accessToken ?? null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = subscribeSession((session) => {
      setAccessToken(session?.accessToken ?? null);
      setUser(session?.user ?? null);
      setMemberships(session?.memberships ?? []);
      setLoading(false);
    });

    return unsubscribe;
  }, []);

  useEffect(() => {
    const session = getStoredSession();
    if (!session) {
      setLoading(false);
      return;
    }

    let cancelled = false;
    fetchMe(session.accessToken)
      .then((result) => {
        if (cancelled) {
          return;
        }
        const nextSession: PersistedSession = {
          ...session,
          user: result.user,
          memberships: result.memberships,
        };
        saveStoredSession(nextSession);
      })
      .catch(() => {
        if (cancelled) {
          return;
        }
        clearStoredSession();
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false);
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function login(email: string, password: string) {
    const response = await loginRequest({ email, password });
    const persisted: PersistedSession = {
      accessToken: response.access_token,
      refreshToken: response.refresh_token,
      user: response.user,
      memberships: response.memberships,
    };

    saveStoredSession(persisted);
  }

  function logout() {
    clearStoredSession();
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
